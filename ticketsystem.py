import discord
from discord.interactions import Interaction
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(command_prefix='!', intents=intents)

class BugReportButton(discord.ui.Button):
    def __init__(self, text, buttonStyle):
        super().__init__(label=text, style=buttonStyle)

    async def callback(self, interaction: discord.Interaction):
        if self.label == "Ticket Schließen":
            view = CloseConfirmationView(interaction.channel.id, interaction.guild, interaction.user.id)
            await interaction.response.send_message("Möchtest du das Ticket wirklich schließen?", view=view)
            
        

class CloseConfirmationView(discord.ui.View):
    def __init__(self, channel_id, guild, user_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.guild = guild
        self.user_id = user_id
    
    @discord.ui.button(label="Ja", style=discord.ButtonStyle.danger)
    async def yes_button(self,interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_yes_button(interaction)

    @discord.ui.button(label="Nein", style=discord.ButtonStyle.success)
    async def no_button(self,interaction: discord.Interaction,button=discord.ui.Button):
        await self.handle_no_button(interaction)

    async def handle_yes_button(self, interaction: discord.Interaction): 
        ticket_category_id = 1142916966298943614
        if interaction.channel.category_id == ticket_category_id:
            if interaction.channel.permissions_for(interaction.user).administrator or interaction.user.id == self.user_id:
                closed_category = discord.utils.get(self.guild.categories, name="====[Ticket Closed]====")
                await interaction.response.send_message("Das Ticket wird geschlossen.")
                await interaction.channel.edit(category=closed_category)
                await interaction.channel.set_permissions(interaction.user, overwrite=None)
             
                # Lösche die CloseConfirmationView-Instanz, um die Frage zu entfernen
                self.stop()
            else:
                await interaction.response.send_message("Du hast keine Berechtigung, dieses Ticket zu schließen.", ephemeral=True)
    
    async def handle_no_button(self, interaction: discord.Interaction):  
        await interaction.response.send_message("Ticket bleibt geöffnet", ephemeral=True)

class BugReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BugReportButton("Ticket Schließen", discord.ButtonStyle.red))
        


class BugReport(discord.ui.Modal, title="Report a Bug"):
        server_name = discord.ui.TextInput(custom_id="servername",label="Server Name",placeholder="z.B. Server 1",required=True,max_length=20,style=discord.TextStyle.short)
        time = discord.ui.TextInput(custom_id="time",label="Datum und Uhrzeit",placeholder="z.B. 01.01.2023 ; 00:00",required=True,max_length=20,style=discord.TextStyle.short)
        abteilung = discord.ui.TextInput(custom_id="kurzbeschreibung",label="Kurzbeschreibung",placeholder="Mapfehler, Game Bug",max_length=20,required=True,style=discord.TextStyle.short)
        beschreibung = discord.ui.TextInput(custom_id="beschreibung",label="Was ist genau Passiert?",placeholder="Was und wie ist es passiert?",required=True,min_length=100,max_length=1000,style=discord.TextStyle.paragraph)
        
        async def on_submit(self, interaction: discord.Interaction):
            user = interaction.user

            # Channel erstellen
            ticket_channel = await interaction.guild.create_text_channel(f"ticket-{self.abteilung.value}", category=discord.utils.get(interaction.guild.categories, name="====[Tickets]===="))

            # Embed erstellen
            embed = discord.Embed(title="**Bug Report**", color=discord.Color.red())
            embed.add_field(name="Server Name", value=self.server_name.value, inline=False)
            embed.add_field(name="Datum und Uhrzeit", value=self.time.value, inline=False)
            embed.add_field(name="Beschreibung", value=self.beschreibung.value, inline=False)
            embed.add_field(name="Abteilung", value=self.abteilung.value, inline=False)

            # Nachricht in den Channel senden
            await ticket_channel.send(embed=embed)
            await ticket_channel.send(view=BugReportView())

            # Benutzer Berechtigungen setzen
            await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)

            # Ping the @team role in the channel
            team_role = discord.utils.get(interaction.guild.roles, name="Team")  # Replace "team" with the actual role name
            if team_role:
                await ticket_channel.send(f":computer: Ein {team_role.mention}-Mitglied wird sich gleich um dich kümmern {user.mention} :computer:")

            await interaction.response.send_message(f"Ticket wurde erstellt und verschoben. Channel #ticket-{self.abteilung.value}", ephemeral=True)

class BugReport(discord.ui.Modal, title="Feedback Request"):
        titel = discord.ui.TextInput(custom_id="titel",label="Titel",placeholder="z.B. Mehr Ingame Events",required=True,max_length=20,style=discord.TextStyle.short)
        server= discord.ui.TextInput(custom_id="server",label="Server",placeholder="Betroffener Server",max_length=20,required=False,style=discord.TextStyle.short)
        beschreibung = discord.ui.TextInput(custom_id="beschreibung",label="Was genau wünscht du dir?",placeholder="Was fehlt dir?",required=True,max_length=1000,style=discord.TextStyle.paragraph)
        
        async def on_submit(self, interaction: discord.Interaction):
            user = interaction.user

            # Channel erstellen
            ticket_channel = await interaction.guild.create_text_channel(f"ticket-{self.abteilung.value}", category=discord.utils.get(interaction.guild.categories, name="====[Tickets]===="))

            # Embed erstellen
            embed = discord.Embed(title="**Bug Report**", color=discord.Color.red())
            embed.add_field(name="Server Name", value=self.server_name.value, inline=False)
            embed.add_field(name="Datum und Uhrzeit", value=self.time.value, inline=False)
            embed.add_field(name="Beschreibung", value=self.beschreibung.value, inline=False)
            embed.add_field(name="Abteilung", value=self.abteilung.value, inline=False)

            # Nachricht in den Channel senden
            await ticket_channel.send(embed=embed)
            await ticket_channel.send(view=BugReportView())

            # Benutzer Berechtigungen setzen
            await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)

            # Ping the @team role in the channel
            team_role = discord.utils.get(interaction.guild.roles, name="Team")  # Replace "team" with the actual role name
            if team_role:
                await ticket_channel.send(f":computer: Ein {team_role.mention}-Mitglied wird sich gleich um dich kümmern {user.mention} :computer:")

            await interaction.response.send_message(f"Ticket wurde erstellt und verschoben. Channel #ticket-{self.abteilung.value}", ephemeral=True)

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="bug-report", description="Melde uns ein Bug")
    async def bugreport(self, interaction:discord.Interaction):
        await interaction.response.send_modal(BugReport())

    @app_commands.command(name="feature-request",description="Du wünscht dir was ? Sag es uns!")
    async def featurerequest(self,interaction:discord.Interaction):
        await interaction.response.send_modal(FeatureRequest())

    @app_commands.command(name="user-add")
    @app_commands.checks.has_role("Team")
    async def ticket_add_member(self, interaction: discord.Interaction, member: discord.Member):
        ticket_category_id = 1142916966298943614  # Hier die ID deiner Ticket-Kategorie eintragen

        if interaction.channel.category_id == ticket_category_id:
            await interaction.response.send_message(f"{member.mention} wurde zum Ticket hinzugefügt.")
            await interaction.channel.set_permissions(member, read_messages=True)
        else:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Ticket-Kanal verwendet werden.")

def setup(bot):
    bot.add_cog(TicketCog(bot))