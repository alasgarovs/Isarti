from kivy.lang import Builder
import os


def load_all_kv_files():
    """Load KV files from separate directory"""
    kv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kv_files')
    common_kv = os.path.join(kv_dir, 'common.kv')
    Builder.load_file(common_kv)
    
    # Load screen files
    for screen in ['login', 'home', 'profile', 'about', 'connection', 'session', 'workspace', 'navigation']:
        kv_file = os.path.join(kv_dir, f'{screen}.kv')
        if os.path.exists(kv_file):
            Builder.load_file(kv_file)
        else:
            print(f"Missing KV file: {kv_file}")