"""
Pagination utilities for API endpoints.

This module provides reusable pagination functionality for list endpoints.
"""

from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


def paginate_query(query, page: int, page_size: int):
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated query result
    """
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def calculate_total_pages(total: int, page_size: int) -> int:
    """
    Calculate total number of pages.
    
    Args:
        total: Total number of items
        page_size: Items per page
        
    Returns:
        Total number of pages
    """
    if page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size