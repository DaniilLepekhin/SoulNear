from typing import Dict, Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey
import database.repository.aiogram_state as aiogram_state


class MyStorage(BaseStorage):
    async def close(self):
        pass

    async def set_state(self, key: StorageKey, state: State | None = None) -> None:
        user_id = key.user_id
        state_name = state.state if state else None

        await aiogram_state.update_state(user_id=user_id, state=state_name)

    async def get_state(self, key: StorageKey) -> State | None:
        user_id = key.user_id
        user = await aiogram_state.get(user_id=user_id)

        if user:
            if user.state:
                state_group, state_name = user.state.split(':')

                return State(group_name=state_group,
                             state=state_name)
            else:
                return None

        await aiogram_state.new(user_id=user_id)

        return None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        user_id = key.user_id

        await aiogram_state.update_data(user_id=user_id, data=data)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        user_id = key.user_id
        user = await aiogram_state.get(user_id=user_id)

        if user.data:
            return user.data

        return {}

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = key.user_id

        user = await aiogram_state.get(user_id=user_id)

        user.data.update(data)
        await aiogram_state.update_data(user_id=user_id, data=user.data)

        return user.data

    async def clear(self, key: StorageKey) -> None:
        user_id = key.user_id

        await aiogram_state.update_state(user_id=user_id, state=None)
        await aiogram_state.update_data(user_id=user_id, data={})

