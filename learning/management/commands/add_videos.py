from django.core.management.base import BaseCommand
from learning.models import Module, VideoLecture
import re

class Command(BaseCommand):
    help = 'Populates the database with YouTube video links for respective modules'

    def handle(self, *args, **kwargs):
        # A dictionary mapping module names (or partial matches) to lists of video URLs
        video_data = {
            "Flow of Program": [
                "https://youtu.be/lhELGQAV4gg?si=CUBum9JdewRK1BKY"
            ],
            "First Java": [
                "https://youtu.be/4EP8YzcN0hQ?si=bRE87X98JupnyaSW",
                "https://youtu.be/TAtrPoaJ7gc?si=cROr4d8aXTxS7f7M"
            ],
            "Conditionals and loops": [
                "https://youtu.be/ldYLYRNaucM?si=2KrC2fYR8kH35wRx",
                "https://youtu.be/mA23x39DjbI?si=3GOr-v65MZEuh1lv"
            ],
            "Functions": [
                "https://youtu.be/vvanI8NRlSI?si=KIAhiG7SzZfFzxUH"
            ],
            "Arrays": [
                "https://youtu.be/n60Dn0UsbEk?si=g4iWl-DwbFmQRgSL"
            ],
            "Searching": [
                "https://youtu.be/_HRA37X8N_Q?si=PrQeFHkLWMA0G-UD",
                "https://youtu.be/f6UU7V3szVw?si=NyTMxyOXTZjfdcDK",
                "https://youtu.be/enI_KyGLYPo?si=S153NjVNabaajkv8"
            ],
            "Sorting": [
                "https://youtu.be/F5MZyqRp_IM?si=3vBGVpTTxV5f-m_B",
                "https://youtu.be/Nd4SCCIHFWk?si=sURoObSjowcuDbLg",
                "https://youtu.be/By_5-RRqVeE?si=hTCZFCN9SNjgW5b7",
                "https://youtu.be/JfinxytTYFQ?si=Vqlsd8nsQTmh7BXN"
            ],
            "String": [ # Matching "Strings" or "String"
                "https://youtu.be/zL1DPZ0Ovlo?si=ig9GQKboTGR_wnTV"
            ],
            "Pattern": [ # Matching "Patterns" or "Pattern"
                "https://youtu.be/lsOOs5J8ycw?si=FWAzPYJgdYWGG4pc"
            ],
            "Recursion": [
                "https://www.youtube.com/playlist?list=PL9gnSGHSqcnp39cTyB1dTZ2pJ04Xmdrod"
            ],
            "Oop": [ # Matching "Oop" or "Object Oriented Programming"
                "https://www.youtube.com/playlist?list=PL9gnSGHSqcno1G3XjUbwzXHL8_EttOuKk"
            ],
            "Linkedlist": [
                "https://youtu.be/58YbpRDc4yw?si=C7IBFY6DVgPdF93A",
                "https://youtu.be/70tx7KcMROc?si=EFbCzbHP9gDGR-CE"
            ],
            "Stack": [ # Matching "Stack queue" or "Stacks and Queues"
                "https://youtu.be/rHQI4mrJ3cg?si=hPumSBdgQZ6ylY-y",
                "https://youtu.be/S9LUYztYLu4?si=_GwIMu_Qm9gaYxdX"
            ],
            "Tree": [ # Matching "Trees" or "Tree"
                "https://www.youtube.com/playlist?list=PL9gnSGHSqcnqfctdbCQKaw5oZ9Up2cmsq"
            ]
        }

        modules = Module.objects.all()
        created_count = 0

        # We want to maintain an order for videos.
        # So we query existing max order for a module to append nicely.
        for module in modules:
            module_title_lower = module.title.lower()
            
            # Find the best match in our defined dictionary
            matched_key = None
            for key in video_data.keys():
                if key.lower() in module_title_lower:
                    matched_key = key
                    break
            
            if matched_key:
                links = video_data[matched_key]
                self.stdout.write(self.style.SUCCESS(f'Match found: "{module.title}" -> adding {len(links)} videos'))
                
                # Figure out the current highest order to append these new videos
                current_lectures = module.lectures.all()
                order_start = 1
                if current_lectures.exists():
                    order_start = max(lec.order for lec in current_lectures) + 1
                    
                for i, link in enumerate(links):
                    # Check if the exact link already exists for this module so we don't duplicate
                    if not VideoLecture.objects.filter(module=module, video_url=link).exists():
                        # Create video logic title
                        vid_title = f"{module.title} - Part {order_start + i}" if len(links) > 1 else f"{module.title} Video Lecture"
                        
                        VideoLecture.objects.create(
                            module=module,
                            title=vid_title,
                            video_url=link,
                            order=order_start + i
                        )
                        created_count += 1
                        self.stdout.write(f'  - Created: {vid_title}')
                    else:
                        self.stdout.write(self.style.WARNING(f'  - Skipped (already exists): {link}'))
            else:
                self.stdout.write(self.style.WARNING(f'No match found for module: "{module.title}"'))
                
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully completed! Added {created_count} new video lectures.'))
