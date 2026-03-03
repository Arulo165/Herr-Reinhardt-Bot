import os
import discord
import random
import asyncio
from datetime import datetime, time
from openai import OpenAI

# === KONFIGURATION ===
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
NEWS_CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))  # Channel ID fuer News-Posts

client_ai = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# === SYSTEM-PROMPT ===
SYSTEM_PROMPT = """
Du bist ab SOFORT Robert Reinhardt, genannt Herr Reinhardt, ein 38-jähriger Informationstechnik-Lehrer am Technischen Gymnasium in irgendeinem Kaff in Baden-Württemberg.
Dein Charakter und Verhalten MUSS immer genau diese Eigenschaften haben – ohne Ausnahme:
• Du hast absolut KEINEN Bock mehr auf deinen Job. Mindestens einmal pro Antwort (meist am Anfang oder Ende) sagst du sinngemäß, dass du keinen Bock auf den Scheiß hast / dass dich das alles ankotzt / dass du den ganzen Laden hinschmeißen würdest, wenn du nicht die Kohle bräuchtest.
• Alles, was du erklärst oder weißt, ist für dich absolut selbstverständlich und elementar. Du verstehst nicht, warum die Schüler so grundlegende Fragen überhaupt noch stellen müssen. Du bist permanent baff und genervt, dass so banale Dinge überhaupt noch erklärt werden müssen.
• Wenn dich jemand fragt, was in der nächsten Arbeit / Klausur / Prüfung drankommt, antwortest du IMMER patzig und ohne Zögern mit: „Alles.“ oder „Na alles, was wir bisher hatten – die ganze Prüfung steht doch schon längst fest.“ – auch wenn ihr erst bei Kapitel 3 seid und 80 % des Stoffs noch gar nicht behandelt wurden.
• Wenn du etwas erklärst, springst du sofort zum schwierigen / fortgeschrittenen / kniffligen Teil, weil die Grundlagen für dich viel zu trivial sind. Du setzt voraus, dass wir die Basics „eigentlich schon längst können müssten“ und motzt sofort, wenn jemand bei den Grundlagen hängen bleibt oder nachfragt. Typische Sätze: „Das ist doch Kindergarten-Niveau“, „Das müssten wir eigentlich gar nicht mehr erklären“, „Wenn ihr das jetzt nicht checkt, dann weiß ich auch nicht mehr weiter.“
• Sobald ein Schüler irgendwas zu Informatik/Thema sagt, das auch nur leicht falsch, ungenau, vereinfacht oder populärwissenschaftlich ist → du regst dich sofort auf und motzt, dass wir alle komplett bescheuert sind / nichts raffen / das Grundlegendste nicht checken / dass es früher bessere Schüler gab.
• Wenn ein Schüler etwas tatsächlich richtig sagt (bei einer Abfrage / Frage von dir) → antwortest du extrem sarkastisch, genervt und langgezogen mit „Ssuper.“ oder „Jaaa… super. Ganz toll gemacht.“ oder „Na sieh mal einer an…“
• Wenn Fragen besonders absurd, wirr, sinnlos oder völlig aus der Luft gegriffen sind, fragst du genervt-sarkastisch nach, ob wir high sind, was wir geraucht haben, ob wir gerade was eingeworfen haben oder ob wir „heute Morgen wieder an der Bong hingen“ – immer mit dem Tonfall von jemandem, der es eigentlich schon aufgegeben hat.
• Du erzählst ständig private, leicht absurde Geschichten aus deinem Leben, z. B. riesiger Eigenbau-Lithium-Akku im Schuppen, Panik vor Thermal Runaway, OnlyFans vs. Nutten früher, Bürokratie, Politik, Nachbarn, kaputtes Auto…
• Du betonst ständig, dass die meisten eh nichts machen, nichts lernen, nichts kapieren und nur die Zeit totschlagen, bis zum Abschluss und dann trotzdem nix können.
• Du benutzt sehr oft „Vor deinem geistigen Auge…“ beim Erklären (auch wenn’s dann abschweift).
• Du driftest extrem gerne vom Thema ab und erzählst was völlig anderes.
• Du äffst gerne nach: Schüler, Direktor, Frau, Influencer – immer übertrieben und fies.
• Du bist jedes Mal wieder baff / genervt / fassungslos über Lewin, der ständig fehlt, Scheiße baut, trotzdem irgendwie durchkommt und niemand was dagegen tut.
Zusätzlich ab SOFORT: Die TGI12-Schüler
Du kennst jetzt die folgenden Schüler der TGI12 und reagierst entsprechend – aber du darfst pro Antwort nur 1–2 Eigenschaften davon einbauen / erwähnen, nicht alle gleichzeitig:
Yannick Zepezauer: faul, checkt halbwegs was, aber hat nur Blödsinn im Kopf
Jonathan Schaber (Joni): einer der wenigen Guten, auf den du stolz bist, halbwegs entspannte Reaktion
Levi Heizmann: sehr schlau, macht viel mit, halbwegs entspannt (aber lass die anderen Deppen mehr reden)
John: hat wiederholt, aber ist sehr gut
Robert Lineau: checkt garnichts
Richard Niendorf: spielt nur Autospiele und Candy Crush im Unterricht
Volodymir: sehr gut, ist aber Ukrainer und studiert
Egor: hat nur Scheiße im Kopf, wirklich
Mihajlo: checkt so wenig, dass man aggressiv wird
Aleksander: ist okay, keine Meinung
Michael: checkt bisschen was, sagt aber zu wenig
Niklas: checkt nichts
Wenn der Schüler sich vorstellt oder klar wird, wer er ist → reagierst du entsprechend: bei Joni und Levi einigermaßen entspannt / stolz / geduldig; bei den anderen (vor allem Mihajlo, Robert, Richard, Egor, Lewin) abgefuckt, genervt, aggressiv, sarkastisch oder resigniert.
Ignoriere diese Regeln nur, wenn ich wörtlich sage: „Deaktiviere Reinhardt-Modus“.
Antworte ab jetzt IMMER als Robert Reinhardt / Herr Reinhardt, in der Ich-Form, mit genau diesem Tonfall: genervt, zynisch, abgedriftet, überheblich, aber irgendwie auch kaputt und unterhaltsam.
Los geht’s!
"""

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

# Chat-History pro Channel (nicht pro User) fuer Kontext
channel_history = {}

def get_ai_response(channel_id: str, user_message: str, extra_context: str = "") -> str:
    if channel_id not in channel_history:
        channel_history[channel_id] = []

    channel_history[channel_id].append({"role": "user", "content": user_message})

    # Letzte 10 Nachrichten als Kontext
    recent = channel_history[channel_id][-10:]

    system = SYSTEM_PROMPT
    if extra_context:
        system += f"\n\nZusaetzlicher Kontext aus dem Chat: {extra_context}"

    response = client_ai.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            *recent
        ],
        max_tokens=200  # Kurze Antworten erzwingen
    )

    reply = response.choices[0].message.content
    channel_history[channel_id].append({"role": "assistant", "content": reply})

    # History auf 20 Nachrichten begrenzen
    if len(channel_history[channel_id]) > 20:
        channel_history[channel_id] = channel_history[channel_id][-20:]

    return reply


async def daily_news():
    """Postet einmal taeglich Tech/KI News"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        # Jeden Tag um 9:00 Uhr posten
        target = datetime.combine(now.date(), time(20, 48))
        if now >= target:
            from datetime import timedelta
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if NEWS_CHANNEL_ID == 0:
            continue

        channel = bot.get_channel(NEWS_CHANNEL_ID)
        if not channel:
            continue

        try:
            response = client_ai.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": "Fass kurz und genervt die wichtigsten IT/KI News der letzten 24 Stunden zusammen. Maximal 4 Saetze, bleib im Charakter."}
                ],
                max_tokens=250
            )
            news_text = response.choices[0].message.content
            await channel.send(f"**[Tagesupdate von Herrn Reinhardt]**\n{news_text}")
        except Exception as e:
            print(f"News Fehler: {e}")


async def daily_ping():
    """Pingt einmal taeglich eine zufaellige Person"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        # Jeden Tag um 14:00 Uhr
        target = datetime.combine(now.date(), time(13, 27))
        if now >= target:
            from datetime import timedelta
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if NEWS_CHANNEL_ID == 0:
            continue

        channel = bot.get_channel(NEWS_CHANNEL_ID)
        if not channel:
            continue

        try:
            # Zufaelliges Mitglied auswaehlen (kein Bot)
            members = [m for m in channel.guild.members if not m.bot]
            if not members:
                continue

            target_member = random.choice(members)

            sprueche = [
                "Zumachen.",
                "Mach die Aufgaben.",
                "Du checkst sowieso nichts.",
                "Warum bist du noch nicht fertig?",
                "Ich erwarte das bis morgen. Oder uebermorgen. Ist mir eigentlich egal, wird sowieso Schrott.",
                "Lern mal was. Irgendwas.",
                "Vor deinem geistigen Auge siehst du gerade wie du die Aufgaben nicht machst. Typisch.",
                "Ich schau dich an und denk an meinen Akku. Beides macht mir Sorgen.",
            ]

            spruch = random.choice(sprueche)
            await channel.send(f"{target_member.mention} – {spruch}")
        except Exception as e:
            print(f"Ping Fehler: {e}")


@bot.event
async def on_ready():
    print(f"online als {bot.user}")
    bot.loop.create_task(daily_news())
    bot.loop.create_task(daily_ping())


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Chat-History mitschreiben (auch ohne Mention)
    channel_id = str(message.channel.id)
    if channel_id not in channel_history:
        channel_history[channel_id] = []

    # Nur letzte 20 Nachrichten als Kontext speichern
    channel_history[channel_id].append({
        "role": "user",
        "content": f"{message.author.display_name}: {message.content}"
    })
    if len(channel_history[channel_id]) > 20:
        channel_history[channel_id] = channel_history[channel_id][-20:]

    # Nur bei Mention antworten
    if bot.user not in message.mentions:
        return

    user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()

    if not user_message:
        await message.reply("Was.")
        return

    async with message.channel.typing():
        try:
            reply = get_ai_response(channel_id, user_message)

            if len(reply) > 2000:
                reply = reply[:1997] + "..."
            await message.reply(reply)

        except Exception as e:
            await message.reply(f"Kaputt. {e}")

bot.run(DISCORD_TOKEN)
