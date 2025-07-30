"""
Bot test fixtures and factories.
"""
from typing import Dict, Any, List
from app.models.bot import Bot, BotPermission
from app.models.user import User


class BotFactory:
    """Factory for creating test bots."""
    
    @staticmethod
    def create_bot_data(
        name: str = "Test Bot",
        description: str = "A test bot",
        system_prompt: str = "You are a helpful assistant",
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """Create bot data dictionary."""
        return {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "is_public": is_public
        }
    
    @staticmethod
    def create_bot(
        db_session,
        owner: User,
        name: str = "Test Bot",
        description: str = "A test bot",
        system_prompt: str = "You are a helpful assistant",
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        is_public: bool = False
    ) -> Bot:
        """Create a bot in the database with owner permission."""
        bot = Bot(
            name=name,
            description=description,
            system_prompt=system_prompt,
            owner_id=owner.id,
            llm_provider=llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            is_public=is_public
        )
        db_session.add(bot)
        db_session.flush()  # Get the bot ID
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=bot.id,
            user_id=owner.id,
            role="owner",
            granted_by=owner.id
        )
        db_session.add(owner_permission)
        
        db_session.commit()
        db_session.refresh(bot)
        return bot
    
    @staticmethod
    def create_bot_with_permissions(
        db_session,
        owner: User,
        collaborators: List[tuple] = None,
        **bot_kwargs
    ) -> Bot:
        """Create a bot with multiple user permissions."""
        bot = BotFactory.create_bot(db_session, owner, **bot_kwargs)
        
        if collaborators:
            for user, role in collaborators:
                permission = BotPermission(
                    bot_id=bot.id,
                    user_id=user.id,
                    role=role,
                    granted_by=owner.id
                )
                db_session.add(permission)
        
        db_session.commit()
        return bot


# Common bot configurations
SAMPLE_BOTS = [
    {
        "name": "Customer Support Bot",
        "description": "Handles customer inquiries",
        "system_prompt": "You are a helpful customer support assistant",
        "llm_provider": "openai",
        "llm_model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500
    },
    {
        "name": "Creative Writing Bot",
        "description": "Helps with creative writing tasks",
        "system_prompt": "You are a creative writing assistant",
        "llm_provider": "anthropic",
        "llm_model": "claude-3-sonnet-20240229",
        "temperature": 0.9,
        "max_tokens": 2000
    },
    {
        "name": "Code Review Bot",
        "description": "Reviews code and provides feedback",
        "system_prompt": "You are a code review assistant",
        "llm_provider": "openai",
        "llm_model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 1500
    }
]