from django.urls import path
from django.contrib import admin
from Sudoku import views

urlpatterns = [
    path('size/', views.size_view, name='size'),
    path('level/', views.level_view, name='level'),  
    path('play/', views.grid_view, name='play'),  
    path('', views.index_view, name='home'),  
    path('solver/', views.solver_view, name='solver'),  
    path('save-game-state/', views.save_game_state, name='save_game_state'),
    path('change-username/', views.change_username, name='change_username'),
    path('delete-profile/', views.delete_profile, name='delete_profile'),
    path('logout/', views.custom_logout, name='logout'),
    path('login/', views.view_login, name='login'),
    path('solve-sudoku/', views.solve_sudoku, name='solve_sudoku'),
    path('sudoku/generate/', views.sudokuGenerate, name='generate_sudoku'),
    path('set-difficulty/', views.set_difficulty, name='set_difficulty'),
    path('get-game-state/', views.get_game_state, name='get_game_state'),
        path('check-game-state/', views.check_game_state, name='check_game_state'),
]
