import re

# Read the current script
with open("enhanced_willspub_sync.py", "r") as f:
    content = f.read()

# Find and replace the download_flyer method
old_method = '''    def download_flyer(self, event_url, event_title):
        """Download show flyer from event page"""
        try:
            print(f"🖼️  Downloading flyer for: {event_title}")
            response = self.session.get(event_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for event images
            flyer_urls = []

            # Check for featured images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '').lower()

                # Look for event flyers (usually larger images)
                if any(keyword in src.lower() for keyword in ['event', 'show', 'flyer', 'poster']):
                    flyer_urls.append(urljoin(event_url, src))
                elif any(keyword in alt for keyword in ['flyer', 'poster', 'show']):
                    flyer_urls.append(urljoin(event_url, src))
                elif img.get('width') and int(img.get('width', 0)) > 400:  # Large images likely flyers
                    flyer_urls.append(urljoin(event_url, src))

            # If no specific flyers found, get the first large image
            if not flyer_urls:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if src and not src.startswith('data:'):
                        flyer_urls.append(urljoin(event_url, src))
                        break'''

new_method = '''    def download_flyer(self, event_url, event_title):
        """Download show flyer from event page"""
        try:
            print(f"🖼️  Downloading flyer for: {event_title}")
            response = self.session.get(event_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for event images - prioritize Open Graph meta tags
            flyer_urls = []

            # First, check Open Graph meta tags (most reliable for event flyers)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                og_url = og_image.get('content')
                # Skip default Will's Pub logo
                if 'wills-pub-logo' not in og_url.lower():
                    flyer_urls.append(og_url)
                    print(f"📸 Found OG image: {og_url}")

            # If no OG image or it's the logo, check for other meta images
            if not flyer_urls:
                twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
                if twitter_image and twitter_image.get('content'):
                    twitter_url = twitter_image.get('content')
                    if 'wills-pub-logo' not in twitter_url.lower():
                        flyer_urls.append(twitter_url)
                        print(f"📸 Found Twitter image: {twitter_url}")

            # Fallback: Look for large images in the page content
            if not flyer_urls:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    alt = img.get('alt', '').lower()

                    # Skip logos and small images
                    if 'logo' in src.lower() or 'logo' in alt:
                        continue

                    # Look for event flyers (usually larger images)
                    if any(keyword in src.lower() for keyword in ['event', 'show', 'flyer', 'poster']):
                        flyer_urls.append(urljoin(event_url, src))
                    elif any(keyword in alt for keyword in ['flyer', 'poster', 'show']):
                        flyer_urls.append(urljoin(event_url, src))
                    elif img.get('width') and int(img.get('width', 0)) > 400:  # Large images likely flyers
                        flyer_urls.append(urljoin(event_url, src))

                if flyer_urls:
                    print(f"📸 Found fallback image: {flyer_urls[0]}")'''

# Replace the method
content = content.replace(old_method, new_method)

# Write the updated script
with open("enhanced_willspub_sync.py", "w") as f:
    f.write(content)

print("✅ Updated flyer detection logic to prioritize Open Graph meta tags")
