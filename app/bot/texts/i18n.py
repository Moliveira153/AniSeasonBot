"""Internationalization service."""

from __future__ import annotations

from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "pt-BR": {
        "welcome": (
            "👋 Bem-vindo ao Anime Season Tracker!\n\n"
            "Acompanhe animes da temporada atual e receba notificações sobre "
            "novos episódios, mudanças de horário, hiatos e muito mais.\n\n"
            "Use os botões abaixo ou os comandos do menu para navegar."
        ),
        "choose_language": "🌐 Escolha seu idioma:",
        "choose_timezone": "🕐 Escolha seu fuso horário:",
        "onboarding_season": "Deseja escolher animes da temporada atual?",
        "season_title": "📺 Temporada: {season}",
        "added": "✅ Adicionado à sua lista!",
        "removed": "❌ Removido da sua lista.",
        "already_tracked": "Este anime já está na sua lista.",
        "not_found": "Anime não encontrado.",
        "list_empty": "Sua lista está vazia. Use /temporada para adicionar animes!",
        "my_list": "📋 *Minha Lista* ({count} animes)",
        "search_prompt": "🔍 Digite o nome do anime para buscar:",
        "search_results": "🔍 Resultados para: *{query}*",
        "settings_title": "⚙️ *Configurações*",
        "notifications_paused": "🔕 Notificações pausadas.",
        "notifications_resumed": "🔔 Notificações reativadas.",
        "help": (
            "📖 *Ajuda*\n\n"
            "/start — Iniciar e configurar\n"
            "/temporada — Animes da temporada\n"
            "/buscar — Buscar anime\n"
            "/anime — Detalhes de um anime\n"
            "/minhalista — Sua lista\n"
            "/proximos — Próximos episódios\n"
            "/hoje — Episódios de hoje\n"
            "/semana — Calendário semanal\n"
            "/configuracoes — Preferências\n"
            "/pausar — Pausar notificações\n"
            "/retomar — Reativar notificações\n"
            "/excluirme — Excluir seus dados\n"
            "/ajuda — Esta ajuda"
        ),
        "about": (
            "ℹ️ *Anime Season Tracker v1.0*\n\n"
            "Bot para acompanhamento de animes da temporada.\n"
            "Dados: AniList (principal), Jikan (complementar).\n\n"
            "Desenvolvido com Python, Aiogram e PostgreSQL."
        ),
        "privacy": (
            "🔒 *Política de Privacidade*\n\n"
            "Armazenamos apenas: ID do Telegram, nome, preferências e lista de animes.\n"
            "Não compartilhamos dados com terceiros.\n"
            "Use /excluirme para remover todos os seus dados."
        ),
        "delete_confirm": "⚠️ Tem certeza? Todos os seus dados serão excluídos permanentemente.",
        "delete_done": "✅ Seus dados foram excluídos.",
        "cancelled": "Operação cancelada.",
        "loading": "⏳ Carregando...",
        "error_generic": "❌ Ocorreu um erro. Tente novamente.",
        "maintenance": "🔧 Bot em manutenção. Tente mais tarde.",
        "page_indicator": "Página {page}/{total}",
        "finish_selection": "✅ Finalizar seleção",
        "today_title": "📅 Episódios de hoje",
        "week_title": "📆 Calendário semanal",
        "upcoming_title": "⏭️ Próximos episódios",
        "no_upcoming": "Nenhum episódio próximo na sua lista.",
        "description_truncated": "📝 Descrição (resumida)",
        "show_full_description": "📖 Ver descrição completa",
    },
    "en": {
        "welcome": (
            "👋 Welcome to Anime Season Tracker!\n\n"
            "Track current season anime and get notifications about "
            "new episodes, schedule changes, hiatus, and more.\n\n"
            "Use the buttons below or menu commands to navigate."
        ),
        "choose_language": "🌐 Choose your language:",
        "choose_timezone": "🕐 Choose your timezone:",
        "onboarding_season": "Would you like to pick anime from the current season?",
        "season_title": "📺 Season: {season}",
        "added": "✅ Added to your list!",
        "removed": "❌ Removed from your list.",
        "already_tracked": "This anime is already in your list.",
        "not_found": "Anime not found.",
        "list_empty": "Your list is empty. Use /temporada to add anime!",
        "my_list": "📋 *My List* ({count} anime)",
        "search_prompt": "🔍 Type the anime name to search:",
        "search_results": "🔍 Results for: *{query}*",
        "settings_title": "⚙️ *Settings*",
        "notifications_paused": "🔕 Notifications paused.",
        "notifications_resumed": "🔔 Notifications resumed.",
        "help": (
            "📖 *Help*\n\n"
            "/start — Start and setup\n"
            "/season — Season anime\n"
            "/search — Search anime\n"
            "/anime — Anime details\n"
            "/mylist — Your list\n"
            "/upcoming — Upcoming episodes\n"
            "/today — Today's episodes\n"
            "/week — Weekly calendar\n"
            "/settings — Preferences\n"
            "/pause — Pause notifications\n"
            "/resume — Resume notifications\n"
            "/deleteme — Delete your data\n"
            "/help — This help"
        ),
        "about": (
            "ℹ️ *Anime Season Tracker v1.0*\n\n"
            "Bot for tracking current season anime.\n"
            "Data: AniList (primary), Jikan (fallback).\n\n"
            "Built with Python, Aiogram and PostgreSQL."
        ),
        "privacy": (
            "🔒 *Privacy Policy*\n\n"
            "We only store: Telegram ID, name, preferences and anime list.\n"
            "We do not share data with third parties.\n"
            "Use /deleteme to remove all your data."
        ),
        "delete_confirm": "⚠️ Are you sure? All your data will be permanently deleted.",
        "delete_done": "✅ Your data has been deleted.",
        "cancelled": "Operation cancelled.",
        "loading": "⏳ Loading...",
        "error_generic": "❌ An error occurred. Please try again.",
        "maintenance": "🔧 Bot under maintenance. Try later.",
        "page_indicator": "Page {page}/{total}",
        "finish_selection": "✅ Finish selection",
        "today_title": "📅 Today's episodes",
        "week_title": "📆 Weekly calendar",
        "upcoming_title": "⏭️ Upcoming episodes",
        "no_upcoming": "No upcoming episodes in your list.",
        "description_truncated": "📝 Description (summary)",
        "show_full_description": "📖 Show full description",
    },
}


class I18n:
    def __init__(self, language: str = "pt-BR") -> None:
        self.language = language if language in MESSAGES else "pt-BR"

    def t(self, key: str, **kwargs: Any) -> str:
        messages = MESSAGES.get(self.language, MESSAGES["pt-BR"])
        text = messages.get(key, MESSAGES["en"].get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text

    @staticmethod
    def available_languages() -> list[str]:
        return list(MESSAGES.keys())