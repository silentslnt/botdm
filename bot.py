import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import json

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Storage for pending DM campaigns
pending_campaigns = {}

class EmbedBuilderView(View):
    def __init__(self, ctx, campaign_id):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.campaign_id = campaign_id
        self.campaign = pending_campaigns.get(campaign_id, {
            'title': '',
            'description': '',
            'color': 0x5865F2,
            'thumbnail': None,
            'image': None,
            'footer': None,
            'author_name': None,
            'author_icon': None,
            'fields': [],
            'content': None,
            'targets': 'everyone',
            'target_ids': [],
            'exclude_bots': True
        })
        
    def build_preview_embed(self):
        """Build the preview embed from campaign data"""
        embed = discord.Embed(
            title=self.campaign.get('title') or "Preview Title",
            description=self.campaign.get('description') or "Preview description...",
            color=self.campaign.get('color', 0x5865F2)
        )
        
        if self.campaign.get('thumbnail'):
            embed.set_thumbnail(url=self.campaign['thumbnail'])
        
        if self.campaign.get('image'):
            embed.set_image(url=self.campaign['image'])
        
        if self.campaign.get('footer'):
            embed.set_footer(text=self.campaign['footer'])
        
        if self.campaign.get('author_name'):
            embed.set_author(
                name=self.campaign['author_name'],
                icon_url=self.campaign.get('author_icon') if self.campaign.get('author_icon') else None
            )
        
        for field in self.campaign.get('fields', []):
            embed.add_field(
                name=field.get('name', 'Field'),
                value=field.get('value', 'Value'),
                inline=field.get('inline', False)
            )
        
        return embed
    
    async def update_preview(self, interaction):
        """Update the preview message"""
        embed = self.build_preview_embed()
        
        # Status embed
        status = discord.Embed(
            title="📝 DM Campaign Builder",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        target_text = {
            'everyone': '👤 Everyone',
            'role': '🏷️ Specific Role',
            'members': '👥 Selected Members'
        }
        
        status.add_field(
            name="🎯 Target",
            value=target_text.get(self.campaign.get('targets'), 'Everyone'),
            inline=True
        )
        status.add_field(
            name="🤖 Exclude Bots",
            value="✅ Yes" if self.campaign.get('exclude_bots') else "❌ No",
            inline=True
        )
        status.add_field(
            name="📊 Estimated Recipients",
            value=str(await self.estimate_recipients()),
            inline=True
        )
        
        status.add_field(
            name="🎨 Color",
            value=f"#{self.campaign.get('color', 0x5865F2):06X}",
            inline=True
        )
        status.add_field(
            name="🖼️ Media",
            value=f"Thumbnail: {'✅' if self.campaign.get('thumbnail') else '❌'}\nImage: {'✅' if self.campaign.get('image') else '❌'}",
            inline=True
        )
        status.add_field(
            name="📝 Fields",
            value=f"{len(self.campaign.get('fields', []))} added",
            inline=True
        )
        
        status.set_footer(text="Use buttons below to customize • Click Preview to see result")
        
        await interaction.response.edit_message(embeds=[status, embed], view=self)
    
    async def estimate_recipients(self):
        """Estimate number of recipients"""
        guild = self.ctx.guild
        targets = self.campaign.get('targets')
        exclude_bots = self.campaign.get('exclude_bots')
        
        if targets == 'everyone':
            members = guild.members
        elif targets == 'role':
            role_id = self.campaign.get('target_role_id')
            if role_id:
                role = guild.get_role(role_id)
                members = role.members if role else []
            else:
                members = guild.members
        else:
            members = [guild.get_member(int(mid)) for mid in self.campaign.get('target_ids', [])]
            members = [m for m in members if m]
        
        if exclude_bots:
            members = [m for m in members if not m.bot]
        
        return len(members)
    
    @discord.ui.button(label="📝 Title & Description", style=discord.ButtonStyle.primary, row=0)
    async def edit_title_desc(self, interaction: discord.Interaction, button: Button):
        
        class TitleDescModal(Modal, title="Edit Title & Description"):
            title_input = TextInput(
                label="Embed Title",
                placeholder="Enter embed title...",
                default=self.campaign.get('title', ''),
                required=False,
                max_length=256
            )
            desc_input = TextInput(
                label="Embed Description",
                placeholder="Enter embed description...",
                default=self.campaign.get('description', ''),
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=4000
            )
            content_input = TextInput(
                label="Message Content (outside embed)",
                placeholder="Text that appears before the embed...",
                default=self.campaign.get('content') or '',
                required=False,
                max_length=2000
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                self.campaign['title'] = modal_self.title_input.value
                self.campaign['description'] = modal_self.desc_input.value
                self.campaign['content'] = modal_self.content_input.value or None
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(TitleDescModal())
    
    @discord.ui.button(label="🎨 Color & Style", style=discord.ButtonStyle.secondary, row=0)
    async def edit_color(self, interaction: discord.Interaction, button: Button):
        
        class ColorModal(Modal, title="Edit Color & Style"):
            color_input = TextInput(
                label="Embed Color (Hex without #)",
                placeholder="e.g., FF0000 for red",
                default=f"{self.campaign.get('color', 0x5865F2):06X}",
                required=False,
                max_length=6
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                try:
                    color_hex = modal_self.color_input.value.strip().replace('#', '')
                    self.campaign['color'] = int(color_hex, 16) if color_hex else 0x5865F2
                except ValueError:
                    self.campaign['color'] = 0x5865F2
                
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(ColorModal())
    
    @discord.ui.button(label="🖼️ Media", style=discord.ButtonStyle.secondary, row=0)
    async def edit_media(self, interaction: discord.Interaction, button: Button):
        
        class MediaModal(Modal, title="Add Images"):
            thumbnail_input = TextInput(
                label="Thumbnail URL",
                placeholder="https://example.com/thumbnail.png",
                default=self.campaign.get('thumbnail') or '',
                required=False
            )
            image_input = TextInput(
                label="Large Image URL",
                placeholder="https://example.com/banner.png",
                default=self.campaign.get('image') or '',
                required=False
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                self.campaign['thumbnail'] = modal_self.thumbnail_input.value or None
                self.campaign['image'] = modal_self.image_input.value or None
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(MediaModal())
    
    @discord.ui.button(label="👤 Author & Footer", style=discord.ButtonStyle.secondary, row=1)
    async def edit_author_footer(self, interaction: discord.Interaction, button: Button):
        
        class AuthorFooterModal(Modal, title="Edit Author & Footer"):
            author_name = TextInput(
                label="Author Name",
                placeholder="Displayed at top of embed",
                default=self.campaign.get('author_name') or '',
                required=False,
                max_length=256
            )
            author_icon = TextInput(
                label="Author Icon URL",
                placeholder="Small icon next to author name",
                default=self.campaign.get('author_icon') or '',
                required=False
            )
            footer = TextInput(
                label="Footer Text",
                placeholder="Displayed at bottom of embed",
                default=self.campaign.get('footer') or '',
                required=False,
                max_length=2048
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                self.campaign['author_name'] = modal_self.author_name.value or None
                self.campaign['author_icon'] = modal_self.author_icon.value or None
                self.campaign['footer'] = modal_self.footer.value or None
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(AuthorFooterModal())
    
    @discord.ui.button(label="📋 Add Field", style=discord.ButtonStyle.success, row=1)
    async def add_field(self, interaction: discord.Interaction, button: Button):
        
        class FieldModal(Modal, title="Add Embed Field"):
            field_name = TextInput(
                label="Field Name",
                placeholder="Field title...",
                required=True,
                max_length=256
            )
            field_value = TextInput(
                label="Field Value",
                placeholder="Field content...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1024
            )
            field_inline = TextInput(
                label="Inline? (yes/no)",
                placeholder="yes or no",
                default="no",
                required=False,
                max_length=3
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                self.campaign.setdefault('fields', []).append({
                    'name': modal_self.field_name.value,
                    'value': modal_self.field_value.value,
                    'inline': modal_self.field_inline.value.lower() == 'yes'
                })
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(FieldModal())
    
    @discord.ui.button(label="🗑️ Clear Fields", style=discord.ButtonStyle.danger, row=1)
    async def clear_fields(self, interaction: discord.Interaction, button: Button):
        self.campaign['fields'] = []
        pending_campaigns[self.campaign_id] = self.campaign
        await self.update_preview(interaction)
    
    @discord.ui.button(label="🎯 Target: Everyone", style=discord.ButtonStyle.primary, row=2)
    async def set_target_everyone(self, interaction: discord.Interaction, button: Button):
        self.campaign['targets'] = 'everyone'
        pending_campaigns[self.campaign_id] = self.campaign
        for item in self.children:
            if hasattr(item, 'label') and 'Target:' in str(item.label):
                item.label = f"🎯 Target: Everyone"
        await self.update_preview(interaction)
    
    @discord.ui.button(label="🏷️ Select Role", style=discord.ButtonStyle.secondary, row=2)
    async def select_role(self, interaction: discord.Interaction, button: Button):
        
        # Create role select menu
        options = []
        for role in self.ctx.guild.roles[:25]:  # Discord limit
            if role.name != "@everyone":
                options.append(discord.SelectOption(
                    label=role.name[:100],
                    value=str(role.id),
                    description=f"{len(role.members)} members"
                ))
        
        if not options:
            await interaction.response.send_message("❌ No roles found!", ephemeral=True)
            return
        
        class RoleSelect(Select):
            def __init__(inner_self):
                super().__init__(
                    placeholder="Select a role to DM...",
                    options=options,
                    min_values=1,
                    max_values=1
                )
            
            async def callback(inner_self, select_interaction: discord.Interaction):
                role_id = int(inner_self.values[0])
                self.campaign['targets'] = 'role'
                self.campaign['target_role_id'] = role_id
                pending_campaigns[self.campaign_id] = self.campaign
                
                role = self.ctx.guild.get_role(role_id)
                await select_interaction.response.send_message(
                    f"✅ Target set to role: **{role.name}**",
                    ephemeral=True
                )
                await self.update_preview(select_interaction)
        
        view = View()
        view.add_item(RoleSelect())
        
        await interaction.response.send_message("Select a role:", view=view, ephemeral=True)
    
    @discord.ui.button(label="👥 Select Members", style=discord.ButtonStyle.secondary, row=2)
    async def select_members(self, interaction: discord.Interaction, button: Button):
        
        class MemberInputModal(Modal, title="Select Members"):
            member_ids = TextInput(
                label="Member IDs (comma separated)",
                placeholder="123456789, 987654321, 456789123...",
                style=discord.TextStyle.paragraph,
                required=True
            )
            
            async def on_submit(modal_self, interaction: discord.Interaction):
                ids = [int(id.strip()) for id in modal_self.member_ids.value.split(',') if id.strip().isdigit()]
                self.campaign['targets'] = 'members'
                self.campaign['target_ids'] = ids
                pending_campaigns[self.campaign_id] = self.campaign
                await self.update_preview(interaction)
        
        await interaction.response.send_modal(MemberInputModal())
    
    @discord.ui.button(label="🤖 Toggle Bots", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_bots(self, interaction: discord.Interaction, button: Button):
        self.campaign['exclude_bots'] = not self.campaign.get('exclude_bots', True)
        pending_campaigns[self.campaign_id] = self.campaign
        await self.update_preview(interaction)
    
    @discord.ui.button(label="👁️ Preview", style=discord.ButtonStyle.primary, row=3)
    async def preview(self, interaction: discord.Interaction, button: Button):
        embed = self.build_preview_embed()
        content = self.campaign.get('content')
        
        preview_embed = discord.Embed(
            title="📤 Message Preview",
            description="This is exactly what recipients will see:",
            color=discord.Color.gold()
        )
        
        await interaction.response.edit_message(embeds=[preview_embed, embed], view=self)
    
    @discord.ui.button(label="✅ Start DM Campaign", style=discord.ButtonStyle.success, row=3)
    async def start_campaign(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        # Execute campaign
        await execute_dm_campaign(self.ctx, self.campaign)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        embed = discord.Embed(
            title="❌ Cancelled",
            description="DM campaign has been cancelled.",
            color=discord.Color.red()
        )
        await self.ctx.send(embed=embed)

async def execute_dm_campaign(ctx, campaign):
    """Execute the DM campaign"""
    
    guild = ctx.guild
    targets = campaign.get('targets')
    exclude_bots = campaign.get('exclude_bots', True)
    
    # Get target members
    if targets == 'everyone':
        members = list(guild.members)
    elif targets == 'role':
        role_id = campaign.get('target_role_id')
        role = guild.get_role(role_id) if role_id else None
        members = list(role.members) if role else []
    else:
        members = [guild.get_member(int(mid)) for mid in campaign.get('target_ids', [])]
        members = [m for m in members if m]
    
    # Filter bots if needed
    if exclude_bots:
        members = [m for m in members if not m.bot]
    
    total = len(members)
    
    if total == 0:
        embed = discord.Embed(
            title="❌ No Recipients",
            description="No valid members found to DM.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Build the embed to send
    send_embed = discord.Embed(
        title=campaign.get('title'),
        description=campaign.get('description'),
        color=campaign.get('color', 0x5865F2)
    )
    
    if campaign.get('thumbnail'):
        send_embed.set_thumbnail(url=campaign['thumbnail'])
    
    if campaign.get('image'):
        send_embed.set_image(url=campaign['image'])
    
    if campaign.get('footer'):
        send_embed.set_footer(text=campaign['footer'])
    
    if campaign.get('author_name'):
        send_embed.set_author(
            name=campaign['author_name'],
            icon_url=campaign.get('author_icon') if campaign.get('author_icon') else None
        )
    
    for field in campaign.get('fields', []):
        send_embed.add_field(
            name=field.get('name'),
            value=field.get('value'),
            inline=field.get('inline', False)
        )
    
    content = campaign.get('content')
    
    # Status message
    status_embed = discord.Embed(
        title="📤 DM Campaign in Progress",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    status_embed.add_field(name="Total Recipients", value=str(total), inline=True)
    status_embed.add_field(name="Sent", value="0", inline=True)
    status_embed.add_field(name="Failed", value="0", inline=True)
    status_embed.add_field(name="Progress", value="0%", inline=True)
    
    status_msg = await ctx.send(embed=status_embed)
    
    # Send DMs
    sent = 0
    failed = 0
    
    for i, member in enumerate(members, 1):
        try:
            await member.send(content=content, embed=send_embed)
            sent += 1
        except discord.Forbidden:
            failed += 1
        except discord.HTTPException:
            failed += 1
        except Exception:
            failed += 1
        
        # Update status every 10 messages
        if i % 10 == 0:
            progress = int(i / total * 100)
            status_embed.set_field_at(1, name="Sent", value=str(sent), inline=True)
            status_embed.set_field_at(2, name="Failed", value=str(failed), inline=True)
            status_embed.set_field_at(3, name="Progress", value=f"{progress}%", inline=True)
            await status_msg.edit(embed=status_embed)
        
        # Rate limiting - important!
        await asyncio.sleep(1.5)
    
    # Final status
    status_embed.title = "✅ DM Campaign Complete"
    status_embed.color = discord.Color.green()
    status_embed.set_field_at(1, name="Sent", value=str(sent), inline=True)
    status_embed.set_field_at(2, name="Failed", value=str(failed), inline=True)
    status_embed.set_field_at(3, name="Success Rate", value=f"{(sent/total*100):.1f}%", inline=True)
    
    await status_msg.edit(embed=status_embed)

# === COMMANDS ===

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user}')
    print(f'📊 Servers: {len(bot.guilds)}')

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx):
    """Start the DM campaign builder"""
    
    campaign_id = f"{ctx.guild.id}_{ctx.author.id}_{datetime.utcnow().timestamp()}"
    
    embed = discord.Embed(
        title="📝 DM Campaign Builder",
        description="Create and send DM messages to server members",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="🎯 Getting Started",
        value=(
            "1. Use the buttons below to customize your message\n"
            "2. Set your target audience\n"
            "3. Preview before sending\n"
            "4. Start the campaign"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 Server Stats",
        value=(
            f"Members: {ctx.guild.member_count}\n"
            f"Humans: {len([m for m in ctx.guild.members if not m.bot])}\n"
            f"Bots: {len([m for m in ctx.guild.members if m.bot])}"
        ),
        inline=True
    )
    
    # Preview embed placeholder
    preview_embed = discord.Embed(
        title="Preview Title",
        description="Your message preview will appear here...",
        color=0x5865F2
    )
    
    view = EmbedBuilderView(ctx, campaign_id)
    view.message = await ctx.send(embeds=[embed, preview_embed], view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def dm_quick(ctx, *, message):
    """Quick DM everyone with a simple message"""
    
    members = [m for m in ctx.guild.members if not m.bot]
    total = len(members)
    
    if total == 0:
        await ctx.send("❌ No members to DM")
        return
    
    embed = discord.Embed(
        title="📤 Quick DM Campaign",
        description=f"Sending to {total} members...",
        color=discord.Color.orange()
    )
    
    status = await ctx.send(embed=embed)
    
    sent, failed = 0, 0
    
    for member in members:
        try:
            await member.send(message)
            sent += 1
        except:
            failed += 1
        
        await asyncio.sleep(1.5)
    
    embed.title = "✅ Complete"
    embed.description = f"Sent: {sent} | Failed: {failed}"
    embed.color = discord.Color.green()
    
    await status.edit(embed=embed)

@bot.command()
async def dmhelp(ctx):
    """Show DM bot help"""
    
    embed = discord.Embed(
        title="🤖 DM All Bot - Help",
        description="Mass DM system for Discord servers",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="📝 Commands",
        value=(
            "`!dm` - Open campaign builder\n"
            "`!dm_quick <message>` - Quick simple DM\n"
            "`!dmhelp` - Show this help"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎯 Target Options",
        value=(
            "• **Everyone** - All server members\n"
            "• **Role** - Members with specific role\n"
            "• **Selected** - Specific member IDs"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎨 Embed Features",
        value=(
            "• Custom title & description\n"
            "• Colors (hex codes)\n"
            "• Thumbnail & banner images\n"
            "• Author name & icon\n"
            "• Footer text\n"
            "• Multiple fields\n"
            "• Content outside embed"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚠️ Important Notes",
        value=(
            "• Rate limited to avoid detection\n"
            "• Users with DMs disabled will fail\n"
            "• Exclude bots by default\n"
            "• Preview before sending"
        ),
        inline=False
    )
    
    embed.set_footer(text="DM All Bot © 2026")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))