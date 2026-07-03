"""FSM states for onboarding and search."""

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    language = State()
    timezone = State()
    season_choice = State()
    season_browse = State()


class SearchStates(StatesGroup):
    waiting_query = State()


class AnimeStates(StatesGroup):
    waiting_id_or_name = State()