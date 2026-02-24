"""
Django management command to generate PWA icons from favicon.
Requires Pillow: pip install Pillow
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class Command(BaseCommand):
    help = 'Generate 192x192 and 512x512 PWA icons from favicon'

    def handle(self, *args, **options):
        if not HAS_PIL:
            self.stdout.write(
                self.style.ERROR('Pillow is required. Install with: pip install Pillow')
            )
            return

        base_dir = Path(settings.BASE_DIR)
        static_dir = base_dir / 'core' / 'static' / 'core'
        favicon_path = static_dir / 'favicon_32x32.png'

        if not favicon_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Favicon not found at {favicon_path}')
            )
            return

        # Load favicon
        try:
            favicon = Image.open(favicon_path)
            # Convert to RGBA if needed
            if favicon.mode != 'RGBA':
                favicon = favicon.convert('RGBA')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading favicon: {e}')
            )
            return

        # Generate 192x192 icon
        icon_192 = favicon.resize((192, 192), Image.Resampling.LANCZOS)
        icon_192_path = static_dir / 'icon_192x192.png'
        icon_192.save(icon_192_path, 'PNG')
        self.stdout.write(
            self.style.SUCCESS(f'Created {icon_192_path}')
        )

        # Generate 512x512 icon
        icon_512 = favicon.resize((512, 512), Image.Resampling.LANCZOS)
        icon_512_path = static_dir / 'icon_512x512.png'
        icon_512.save(icon_512_path, 'PNG')
        self.stdout.write(
            self.style.SUCCESS(f'Created {icon_512_path}')
        )

        self.stdout.write(
            self.style.SUCCESS('PWA icons generated successfully!')
        )
