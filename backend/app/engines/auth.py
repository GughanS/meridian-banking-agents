from uuid import UUID


def verify_ownership(resource_customer_id: UUID, current_user_id: UUID) -> bool:
    """Object-level authorization: ensure the resource belongs to the caller."""
    return resource_customer_id == current_user_id
