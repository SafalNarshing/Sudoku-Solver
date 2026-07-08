from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .sudoku_solver import solve_with_comparison
from .puzzleGenerator2 import generate_sudoku
from .models import UserInfo
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
# Create your views here.

SUPPORTED_SIZES = (9, 16)

@csrf_exempt

def index(request):  
    context = {}  
    if request.user.is_authenticated:  
        try:  
            # Retrieve the UserInfo associated with the user  
            user_info = UserInfo.objects.get(user=request.user)  
            context['high_score'] = user_info.high_score or 0
            context['username'] = request.user.username  

            print("User:", request.user)  
            print("Username:", context['username'])  
            print("High Score:", context['high_score']) 
        except UserInfo.DoesNotExist:  
            # If UserInfo doesn't exist, create it with default values
            UserInfo.objects.create(
                user=request.user, 
                username=request.user.username, 
                high_score=0
            )
            context['username'] = request.user.username  
            context['high_score'] = 0  
    return render(request, 'index.html', context)

@login_required  
def change_username(request):  
    if request.method == 'POST':  
        try:  
            # Parse JSON data  
            data = json.loads(request.body)  
            new_username = data.get('username', '').strip()  
            
            # Validate username  
            if not new_username:  
                return JsonResponse({'success': False, 'error': 'Username cannot be empty'})  
            
            # Check if username already exists  
            if User.objects.exclude(pk=request.user.pk).filter(username=new_username).exists():  
                return JsonResponse({'success': False, 'error': 'Username already exists'})  
            
            # Update user's username  
            user = request.user  
            user.username = new_username  
            user.save()  
            
            # Update UserInfo model if it exists  
            user_info, created = UserInfo.objects.get_or_create(user=user)  
            user_info.username = new_username  
            user_info.save()  
            
            return JsonResponse({  
                'success': True,   
                'username': new_username,
                'high_score': user_info.high_score or 0  # Include high score in response
            })  
        
        except Exception as e:  
            return JsonResponse({  
                'success': False,   
                'error': str(e)  
            })  
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.delete()  # This will also delete the associated profile due to CASCADE
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def custom_logout(request):
    logout(request)
    if 'solver' in request.META.get('HTTP_REFERER', ''):
        return redirect('solver')
    return redirect('home')

def view_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        
        if not username or username.strip() == '':
            messages.error(request, 'Username cannot be empty')
            return render(request, 'Sudoku/login.html')
        
        try:
            # Check if username exists
            user = User.objects.filter(username=username.strip()).first()
            
            # If user doesn't exist, create a new non-staff user
            if not user:
                user = User.objects.create_user(
                    username=username.strip(),
                    is_staff=False
                )
            
            # Prevent staff/superuser login
            if user.is_staff:
                messages.error(request, 'Admin users cannot log in through this portal')
                return render(request, 'Sudoku/login.html')
            
            # Create or get UserInfo profile
            user_info, profile_created = UserInfo.objects.get_or_create(
                user=user,
                defaults={
                    'username': username.strip(),
                    'high_score': 0
                }
            )
            
            # Log the user in
            login(request, user)
            
            messages.success(request, 'Login successful!')
            return redirect('level')
        
        except Exception as e:
            print(f"Login error: {e}")
            messages.error(request, f'Login failed: {str(e)}')
            return render(request, 'Sudoku/login.html')
    
    return render(request, 'Sudoku/login.html')

def index_view(request):
    return render(request, 'Sudoku/index.html')

def size_view(request):
    return render(request, 'Sudoku/size.html')

def level_view(request):
    return render(request, 'Sudoku/level.html')

def grid_view(request):
    # Get difficulty/grid size from session or URL parameter
    difficulty = request.session.get('difficulty', 'Easy')  # Default to 'Easy' if not set
    grid_size = request.session.get('grid_size', 9)
    return render(request, 'Sudoku/play.html', {"difficulty": difficulty, "grid_size": grid_size})

@csrf_exempt
@require_POST
def set_difficulty(request):
     try:
        data = json.loads(request.body)  # Parse JSON data from the request
        difficulty = data.get('difficulty')  # Get the difficulty level
        grid_size = data.get('gridSize', 9)
        if grid_size not in SUPPORTED_SIZES:
            return JsonResponse({'success': False, 'error': f'Unsupported grid size: {grid_size}'})
        if difficulty:
            request.session['difficulty'] = difficulty  # Store it in session
            request.session['grid_size'] = grid_size
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No difficulty provided'})
     except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# def login_view(request):
#     return render(request, 'Sudoku/login.html')

def solver_view(request):
    return render(request, 'Sudoku/solver.html')

@csrf_exempt
def sudokuGenerate(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            clues = body.get('clues', 30)  # Default to 30 if not provided
            size = body.get('size', 9)
            if size not in SUPPORTED_SIZES:
                return JsonResponse({'error': f'Unsupported grid size: {size}'}, status=400)

            print(f"Generating {size}x{size} puzzle with {clues} clues")

            puzzle, solution = generate_sudoku(clues, n=size)
            
            print("Generated puzzle structure:")
            for row in puzzle:
                print(row)
            print("Generated solution structure:")
            for row in solution:
                print(row)
            
            return JsonResponse({
                'puzzle': puzzle,
                'solutionBoard': solution  
            })
            
        except Exception as e:
            print(f"Error generating sudoku: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def game_view(request):
    if request.user.is_authenticated:
        game_data = UserInfo.objects.get(user=request.user)
        context = {
            'game_state': game_data.game_state,
            'time': game_data.time,
            'score': game_data.score,
        }
        return render(request, 'sudoku_game.html', context)
    return redirect('login')

@csrf_exempt
def solve_sudoku(request):
    if request.method == 'POST':
        try:
            size = int(request.POST.get('size', 9))
            if size not in SUPPORTED_SIZES:
                return JsonResponse({'solved': False, 'error': f'Unsupported grid size: {size}'})

            board = [[0 for _ in range(size)] for _ in range(size)]
            for row in range(size):
                for col in range(size):
                    cell_name = f'cell_{row}_{col}'
                    value = request.POST.get(cell_name, '').strip()
                    if value and value.isdigit() and 1 <= int(value) <= size:
                        board[row][col] = int(value)
            
            # Solve using both methods and compare
            success, solution, heuristic_time, backtrack_time, dlx_time, backtrack_success, progress = solve_with_comparison(board)

            if success:
                return JsonResponse({
                    'solved': True,
                    'solution': solution,
                    'heuristic_time': round(heuristic_time, 2),
                    'backtrack_time': round(backtrack_time, 2),
                    'backtrack_solved': backtrack_success,
                    'dlx_time': round(dlx_time, 2),  # Include DLX time in the response
                    'progress': progress  # {heuristic, backtrack, dlx}: [(elapsed_ms, cells_filled), ...]
                })
            else:
                return JsonResponse({
                    'solved': False,
                    'error': 'No solution exists'
                })
        except Exception as e:
            print(f"Exception in solve_sudoku: {e}")
            return JsonResponse({
                'solved': False,
                'error': str(e)
            })
    return JsonResponse({
        'solved': False,
        'error': 'Invalid request method'
    })
# load game state
# Add to views.py
@login_required
def save_game_state(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_info = UserInfo.objects.get(user=request.user)

            user_info.current_game_state = data.get('gameBoard')
            user_info.current_solution = data.get('solutionBoard')
            user_info.current_score = data.get('score')
            user_info.current_time = data.get('time')
            user_info.difficulty_level = data.get('difficulty')
            user_info.grid_size = data.get('gridSize', 9)
            user_info.is_game_in_progress = True
            user_info.is_paused = data.get('isPaused', False)

            user_info.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def get_game_state(request):
    try:
        user_info = UserInfo.objects.get(user=request.user)
        if user_info.is_game_in_progress:
            return JsonResponse({
                'status': 'success',
                'gameState': {
                    'gameBoard': user_info.current_game_state,
                    'solutionBoard': user_info.current_solution,
                    'score': user_info.current_score,
                    'time': user_info.current_time,
                    'difficulty': user_info.difficulty_level,
                    'isPaused': user_info.is_paused,  # Add pause state to response
                    'gridSize': user_info.grid_size
                }
            })
        return JsonResponse({'status': 'no_game'})
    except UserInfo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User info not found'})
    
def check_game_state(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'game_in_progress': False})
            
        try:
            user_info = UserInfo.objects.get(user=request.user)
            return JsonResponse({
                'game_in_progress': user_info.is_game_in_progress
            })
        except UserInfo.DoesNotExist:
            return JsonResponse({'game_in_progress': False})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)