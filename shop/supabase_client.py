import os

from supabase import create_client

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            'Supabase credentials are not set. Define SUPABASE_URL and SUPABASE_KEY in your environment.'
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)
