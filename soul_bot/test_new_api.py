"""
Тест нового OpenAI Service

Запуск:
    python test_new_api.py
"""
import asyncio
from bot.services.openai_service import get_chat_completion, build_system_prompt

async def test_system_prompt():
    """Тест построения system prompt"""
    print("=" * 60)
    print("🧪 ТЕСТ 1: Построение system prompt")
    print("=" * 60)
    
    # Тестовый user_id (можно использовать любой из БД)
    test_user_id = 580613548
    
    prompt = await build_system_prompt(
        user_id=test_user_id,
        assistant_type='helper'
    )
    
    print(f"\n📝 System Prompt для user {test_user_id}:")
    print("-" * 60)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 60)
    print(f"✅ Длина промпта: {len(prompt)} символов\n")


async def test_chat_completion():
    """Тест ChatCompletion API"""
    print("=" * 60)
    print("🧪 ТЕСТ 2: ChatCompletion API")
    print("=" * 60)
    
    # Тестовый user_id
    test_user_id = 580613548
    test_message = "Привет! Как дела?"
    
    print(f"\n💬 Отправляем сообщение: '{test_message}'")
    print("⏳ Ждём ответа от OpenAI...")
    
    try:
        response = await get_chat_completion(
            user_id=test_user_id,
            message=test_message,
            assistant_type='helper'
        )
        
        if response:
            print("\n✅ Получен ответ:")
            print("-" * 60)
            print(response)
            print("-" * 60)
        else:
            print("\n❌ Ответ не получен (возможно, ошибка API)")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


async def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║       🧪 ТЕСТИРОВАНИЕ НОВОГО OpenAI SERVICE 🧪              ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Тест 1: System Prompt
    await test_system_prompt()
    
    # Тест 2: ChatCompletion (раскомментируй если хочешь потратить токены)
    # await test_chat_completion()
    
    print("\n")
    print("=" * 60)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)
    print("\n💡 Чтобы протестировать ChatCompletion, раскомментируй")
    print("   test_chat_completion() в функции main()")
    print("\n")


if __name__ == '__main__':
    asyncio.run(main())
