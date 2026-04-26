from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import Depends, HTTPException

from customer_support_agent.core.settings import Settings, get_settings
from customer_support_agent.repositories.sqlite.customer import CustomersRepository
from customer_support_agent.repositories.sqlite.draft import DraftsRepository
from customer_support_agent.repositories.sqlite.tickets import TicketsRepository
from customer_support_agent.services.copilot_service import SupportCopilot
from customer_support_agent.services.draft_service import DraftService
from customer_support_agent.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


@lru_cache
def get_copilot() -> SupportCopilot:
    return SupportCopilot(settings=get_settings())


def get_copilot_or_503() -> SupportCopilot:
    try:
        return get_copilot()
    except Exception:
        logger.exception("copilot.init.error")
        raise HTTPException(status_code=503, detail="AI copilot is currently unavailable")


def get_settings_dep() -> Settings:
    return get_settings()


def get_customers_repository() -> CustomersRepository:
    return CustomersRepository()


def get_tickets_repository() -> TicketsRepository:
    return TicketsRepository()


def get_drafts_repository() -> DraftsRepository:
    return DraftsRepository()


def get_draft_service() -> DraftService:
    return DraftService()


def get_knowledge_service(settings: Settings = Depends(get_settings_dep)) -> KnowledgeService:
    return KnowledgeService(settings=settings)