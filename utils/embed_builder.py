import discord
from typing import Optional, List, Dict

class EmbedBuilder:
    """Helper class for building embeds"""
    
    def __init__(self):
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.color: int = 0x5865F2
        self.thumbnail: Optional[str] = None
        self.image: Optional[str] = None
        self.footer: Optional[str] = None
        self.author_name: Optional[str] = None
        self.author_icon: Optional[str] = None
        self.fields: List[Dict] = []
        self.content: Optional[str] = None
    
    def set_title(self, title: str):
        self.title = title[:256] if title else None
        return self
    
    def set_description(self, description: str):
        self.description = description[:4096] if description else None
        return self
    
    def set_color(self, color: int):
        self.color = color
        return self
    
    def set_color_hex(self, hex_color: str):
        hex_color = hex_color.replace('#', '')
        self.color = int(hex_color, 16)
        return self
    
    def set_thumbnail(self, url: str):
        self.thumbnail = url
        return self
    
    def set_image(self, url: str):
        self.image = url
        return self
    
    def set_footer(self, text: str):
        self.footer = text[:2048] if text else None
        return self
    
    def set_author(self, name: str, icon_url: str = None):
        self.author_name = name[:256] if name else None
        self.author_icon = icon_url
        return self
    
    def add_field(self, name: str, value: str, inline: bool = False):
        self.fields.append({
            'name': name[:256],
            'value': value[:1024],
            'inline': inline
        })
        return self
    
    def set_content(self, content: str):
        self.content = content[:2000] if content else None
        return self
    
    def build(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=self.color
        )
        
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        
        if self.image:
            embed.set_image(url=self.image)
        
        if self.footer:
            embed.set_footer(text=self.footer)
        
        if self.author_name:
            embed.set_author(
                name=self.author_name,
                icon_url=self.author_icon if self.author_icon else discord.Embed.Empty
            )
        
        for field in self.fields:
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field['inline']
            )
        
        return embed
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'description': self.description,
            'color': self.color,
            'thumbnail': self.thumbnail,
            'image': self.image,
            'footer': self.footer,
            'author_name': self.author_name,
            'author_icon': self.author_icon,
            'fields': self.fields,
            'content': self.content
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EmbedBuilder':
        builder = cls()
        builder.title = data.get('title')
        builder.description = data.get('description')
        builder.color = data.get('color', 0x5865F2)
        builder.thumbnail = data.get('thumbnail')
        builder.image = data.get('image')
        builder.footer = data.get('footer')
        builder.author_name = data.get('author_name')
        builder.author_icon = data.get('author_icon')
        builder.fields = data.get('fields', [])
        builder.content = data.get('content')
        return builder