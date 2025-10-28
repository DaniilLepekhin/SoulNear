#!/usr/bin/env python3
"""
🧹 Test Database Cleanup Script

Safely cleans test database for fresh testing runs.

Usage:
    # Clean everything
    python cleanup_test_db.py --all
    
    # Clean specific user
    python cleanup_test_db.py --user-id 123456789
    
    # Clean test users only (prefix "Алексей", "Тест", etc.)
    python cleanup_test_db.py --test-users
    
    # Dry run (show what would be deleted)
    python cleanup_test_db.py --all --dry-run

Safety:
    - Only works with ENV=test (fails on production!)
    - Requires confirmation before deletion
    - Shows statistics before cleanup
"""

import asyncio
import sys
import os
from pathlib import Path

# Get script location and change to soul_bot directory
script_dir = Path(__file__).parent
soul_bot_dir = script_dir.parent
os.chdir(soul_bot_dir)

# Add soul_bot directory to path
sys.path.insert(0, str(soul_bot_dir))

from sqlalchemy import select, delete, func
from database.database import async_session_maker
from database.models import User, UserProfile, ConversationHistory, QuizSession
from config import DATABASE_URL, ENV

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


async def get_database_stats():
    """Get current database statistics"""
    async with async_session_maker() as session:
        users_count = await session.scalar(select(func.count(User.user_id)))
        profiles_count = await session.scalar(select(func.count(UserProfile.user_id)))
        conversations_count = await session.scalar(select(func.count(ConversationHistory.id)))
        quizzes_count = await session.scalar(select(func.count(QuizSession.id)))
        
        return {
            'users': users_count,
            'profiles': profiles_count,
            'conversations': conversations_count,
            'quizzes': quizzes_count
        }


def print_stats(stats: dict, title: str = "Database Statistics"):
    """Print database statistics"""
    print(f"\n{Colors.BOLD}{title}:{Colors.END}")
    print(f"  👤 Users:          {stats['users']}")
    print(f"  🧠 Profiles:       {stats['profiles']}")
    print(f"  💬 Conversations:  {stats['conversations']}")
    print(f"  📝 Quizzes:        {stats['quizzes']}")
    print()


async def cleanup_all_data(dry_run: bool = False):
    """Clean all data from database"""
    if dry_run:
        print_warning("DRY RUN MODE - No data will be deleted")
    
    print_info("Fetching current statistics...")
    before_stats = await get_database_stats()
    print_stats(before_stats, "Before Cleanup")
    
    if before_stats['users'] == 0:
        print_warning("Database is already empty!")
        return
    
    if not dry_run:
        # Confirmation
        print_warning(f"This will DELETE ALL data from test database!")
        confirm = input(f"{Colors.YELLOW}Type 'DELETE ALL' to confirm: {Colors.END}")
        
        if confirm != "DELETE ALL":
            print_error("Cleanup cancelled")
            return
    
    if not dry_run:
        async with async_session_maker() as session:
            # Delete in order (respecting foreign keys)
            print_info("Deleting quiz sessions...")
            await session.execute(delete(QuizSession))
            
            print_info("Deleting conversation history...")
            await session.execute(delete(ConversationHistory))
            
            print_info("Deleting user profiles...")
            await session.execute(delete(UserProfile))
            
            print_info("Deleting users...")
            await session.execute(delete(User))
            
            await session.commit()
            print_success("All data deleted successfully!")
    else:
        print_info("Would delete all records from: quiz_sessions, conversation_history, user_profiles, users")
    
    if not dry_run:
        after_stats = await get_database_stats()
        print_stats(after_stats, "After Cleanup")


async def cleanup_user(user_id: int, dry_run: bool = False):
    """Clean specific user and related data"""
    if dry_run:
        print_warning("DRY RUN MODE - No data will be deleted")
    
    async with async_session_maker() as session:
        # Check if user exists
        user = await session.scalar(select(User).where(User.user_id == user_id))
        
        if not user:
            print_error(f"User {user_id} not found!")
            return
        
        print_info(f"Found user: {user.real_name} (ID: {user_id})")
        
        # Get related data counts
        profile_count = await session.scalar(
            select(func.count(UserProfile.user_id)).where(UserProfile.user_id == user_id)
        )
        conv_count = await session.scalar(
            select(func.count(ConversationHistory.id)).where(ConversationHistory.user_id == user_id)
        )
        quiz_count = await session.scalar(
            select(func.count(QuizSession.id)).where(QuizSession.user_id == user_id)
        )
        
        print(f"\n{Colors.BOLD}Related Data:{Colors.END}")
        print(f"  🧠 Profile:        {profile_count}")
        print(f"  💬 Conversations:  {conv_count}")
        print(f"  📝 Quizzes:        {quiz_count}")
        print()
        
        if not dry_run:
            confirm = input(f"{Colors.YELLOW}Delete this user and all related data? (yes/no): {Colors.END}")
            
            if confirm.lower() != "yes":
                print_error("Cleanup cancelled")
                return
            
            # Delete in order
            print_info("Deleting quiz sessions...")
            await session.execute(delete(QuizSession).where(QuizSession.user_id == user_id))
            
            print_info("Deleting conversation history...")
            await session.execute(delete(ConversationHistory).where(ConversationHistory.user_id == user_id))
            
            print_info("Deleting user profile...")
            await session.execute(delete(UserProfile).where(UserProfile.user_id == user_id))
            
            print_info("Deleting user...")
            await session.execute(delete(User).where(User.user_id == user_id))
            
            await session.commit()
            print_success(f"User {user_id} and all related data deleted successfully!")
        else:
            print_info(f"Would delete user {user_id} and all related records")


async def cleanup_test_users(dry_run: bool = False):
    """Clean users with test names (Алексей, Тест, Test, etc.)"""
    if dry_run:
        print_warning("DRY RUN MODE - No data will be deleted")
    
    test_patterns = ['Алексей', 'Тест', 'Test', 'testuser', 'test_']
    
    async with async_session_maker() as session:
        # Find test users
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        test_users = [
            u for u in users 
            if any(pattern.lower() in (u.real_name or '').lower() for pattern in test_patterns)
        ]
        
        if not test_users:
            print_warning("No test users found!")
            return
        
        print_info(f"Found {len(test_users)} test users:")
        for user in test_users:
            print(f"  - {user.real_name} (ID: {user.user_id})")
        print()
        
        if not dry_run:
            confirm = input(f"{Colors.YELLOW}Delete these {len(test_users)} test users? (yes/no): {Colors.END}")
            
            if confirm.lower() != "yes":
                print_error("Cleanup cancelled")
                return
        
        # Delete each test user
        for user in test_users:
            if dry_run:
                print_info(f"Would delete: {user.real_name} (ID: {user.user_id})")
            else:
                print_info(f"Deleting: {user.real_name} (ID: {user.user_id})...")
                
                # Delete related data
                await session.execute(delete(QuizSession).where(QuizSession.user_id == user.user_id))
                await session.execute(delete(ConversationHistory).where(ConversationHistory.user_id == user.user_id))
                await session.execute(delete(UserProfile).where(UserProfile.user_id == user.user_id))
                await session.execute(delete(User).where(User.user_id == user.user_id))
        
        if not dry_run:
            await session.commit()
            print_success(f"Deleted {len(test_users)} test users successfully!")


def check_safety():
    """Check if it's safe to run cleanup (only on test DB)"""
    print_header("🧹 Test Database Cleanup")
    
    # Check environment
    if ENV != 'test':
        print_error(f"UNSAFE: Current environment is '{ENV}' (not 'test')")
        print_error("This script can ONLY run on test database!")
        print_info("Set ENV=test in your environment or use .env.test")
        sys.exit(1)
    
    print_success(f"Environment: {ENV}")
    print_info(f"Database: {DATABASE_URL[:50]}...")
    
    # Double check database name
    if 'test' not in DATABASE_URL.lower():
        print_warning("Database URL doesn't contain 'test'")
        confirm = input(f"{Colors.YELLOW}Are you SURE this is test database? (yes/no): {Colors.END}")
        if confirm.lower() != "yes":
            print_error("Cleanup cancelled for safety")
            sys.exit(1)


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean test database for fresh testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean everything
  python cleanup_test_db.py --all
  
  # Clean specific user
  python cleanup_test_db.py --user-id 123456789
  
  # Clean test users only
  python cleanup_test_db.py --test-users
  
  # Dry run (preview)
  python cleanup_test_db.py --all --dry-run
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Delete ALL data')
    parser.add_argument('--user-id', type=int, help='Delete specific user')
    parser.add_argument('--test-users', action='store_true', help='Delete users with test names')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    # Check safety first
    check_safety()
    
    # Execute cleanup
    if args.all:
        await cleanup_all_data(dry_run=args.dry_run)
    elif args.user_id:
        await cleanup_user(args.user_id, dry_run=args.dry_run)
    elif args.test_users:
        await cleanup_test_users(dry_run=args.dry_run)
    else:
        parser.print_help()
        print()
        print_error("Please specify cleanup mode: --all, --user-id, or --test-users")
        sys.exit(1)
    
    print_header("✨ Cleanup Complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print_error("Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

