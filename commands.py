import discord
from discord import app_commands
from discord.ext import commands
from tinydb import TinyDB, Query
import os
from discord.ext.commands import Bot

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'empire_db.json')
db = TinyDB(DB_PATH)
members_table = db.table('members')

async def ask_mc_username(member, bot):
    try:
        dm = await member.create_dm()
        await dm.send(
            f"Welcome to the Empire, {member.display_name}! Please reply with your Minecraft username to link your Discord account."
        )
    except Exception as e:
        print(f"Failed to DM {member.display_name}: {e}")

class EmpireCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ranks = [
        app_commands.Choice(name="Soldier", value="Soldier"),
        app_commands.Choice(name="Commander", value="Commander"),
        app_commands.Choice(name="Officer", value="Officer"),
        app_commands.Choice(name="General", value="General"),
    ]

    @app_commands.command(name="add_member", description="Add a Minecraft player linked to a Discord user")
    @app_commands.checks.has_role("Officer")
    @app_commands.describe(
        mc_username="Minecraft username of the player",
        discord_user="Discord user to link (optional)",
        rank="Select the rank"
    )
    @app_commands.choices(rank=ranks)
    async def add_member(
        self,
        interaction: discord.Interaction,
        mc_username: str,
        rank: app_commands.Choice[str],
        discord_user: discord.Member = None
    ):
        # Default discord_user to command user if not provided
        if discord_user is None:
            discord_user = interaction.user

        # Defer the response and send a processing message
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"⏳ Adding **{mc_username}** as **{rank.value}**...", ephemeral=True)

        Member = Query()
        existing = members_table.get(Member.mc_username == mc_username)
        if existing:
            await interaction.followup.send(
                f"⚠️ Minecraft user **{mc_username}** is already registered with rank {existing['rank']}.",
                ephemeral=True
            )
            return

        # Insert into DB
        members_table.insert({
            'mc_username': mc_username,
            'discord_id': discord_user.id,
            'discord_name': discord_user.display_name,
            'rank': rank.value
        })

        # Assign role
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=rank.value)
        if role:
            try:
                await discord_user.add_roles(role, reason="Empire rank assignment")
            except Exception as e:
                await interaction.followup.send(
                    f"⚠️ Could not assign role **{rank.value}** to {discord_user.display_name}: {e}",
                    ephemeral=True
                )
                return
        else:
            await interaction.followup.send(
                f"⚠️ Role **{rank.value}** does not exist in this server. Please create it first.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"✅ Added Minecraft user **{mc_username}** linked to {discord_user.display_name} with rank **{rank.value}** and assigned role."
        )

    @app_commands.command(name="roster", description="Show the empire roster")
    async def roster(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        members = members_table.all()
        if not members:
            await interaction.followup.send("🏰 The empire has no members yet.", ephemeral=True)
            return

        roster_text = "**Empire Roster:**\n" + "\n".join([
            f"- {m['mc_username']} ({m['discord_name']}) | {m['rank']}" for m in members
        ])
        await interaction.followup.send(roster_text, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await ask_mc_username(member, self.bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            # DM context
            Member = Query()
            # Check if this user is already linked
            existing = members_table.get(Member.discord_id == message.author.id)
            if existing and existing.get('mc_username'):
                await message.channel.send("You are already linked to a Minecraft account.")
                return
            # Save the Minecraft username
            mc_username = message.content.strip()
            if not mc_username:
                await message.channel.send("Please provide a valid Minecraft username.")
                return
            # Save or update
            if existing:
                members_table.update({'mc_username': mc_username}, Member.discord_id == message.author.id)
            else:
                members_table.insert({
                    'mc_username': mc_username,
                    'discord_id': message.author.id,
                    'discord_name': message.author.display_name,
                    'rank': 'Soldier'  # Default rank
                })
            await message.channel.send(f"✅ Your Discord is now linked to Minecraft user **{mc_username}**. Welcome!")
            # Optionally assign default role
            guild = discord.utils.get(self.bot.guilds)
            if guild:
                role = discord.utils.get(guild.roles, name="Soldier")
                member = guild.get_member(message.author.id)
                if role and member:
                    try:
                        await member.add_roles(role, reason="Auto-link on join")
                    except Exception as e:
                        print(f"Could not assign role: {e}")

async def setup(bot):
    await bot.add_cog(EmpireCommands(bot))

# Fix code later