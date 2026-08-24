for category_name, items in LAYOUT:
    overwrites = None

    if "ADMIN" in category_name:
        overwrites = admin_overwrites

    category = await guild.create_category(
        category_name,
        overwrites=overwrites,
    )

    for item in items:
        name, key = item[0], item[1]
        kind = item[2] if len(item) > 2 else "text"

        if kind == "voice":
            channel = await guild.create_voice_channel(
                name,
                category=category,
            )
            guild_data["channels"][key] = channel.id
            continue

        perms = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
            )
        }

        if key in {"admin", "confession_logs"}:
            perms = admin_overwrites

        channel = await guild.create_text_channel(
            name,
            category=category,
            overwrites=perms,
        )

        explainer = EXPLAINERS.get(
            key,
            "This channel exists for a reason.",
        )

        await self.safe_pin(channel, explainer)

        if key == "trap":
            await channel.send(
                "Read the pinned message. Type here and you get banned instantly."
            )

        if key == "commands":
            commands_text = (
                "**Bot Commands** 
"
                "`/gif` convert image to gif or make a meme caption\n"
                "`/caption` meme caption image\n"
                "`/play /skip /stop /queue /pause /resume /nowplaying /loop` music\n"
                "`/confess` anonymous confession\n"
                "`/curseboard` curse leaderboard\n"
                "`/daily /rob /bet /rep /profile /age /trivia /rps /numguess "
                "/poll /avatar /serverinfo /userinfo /8ball /coinflip /roll "
                "/remindme /reserved`"
            )

            commands_message = await channel.send(commands_text)

            try:
                await commands_message.pin()
            except Exception:
                pass

            guild_data["commands_message_id"] = commands_message.id

        if key == "curse":
            embed = discord.Embed(
                title="🤬 Curse Leaderboard",
                description="live shameboard",
                color=discord.Color.red(),
            )

            curse_message = await channel.send(embed=embed)
            guild_data["curse_message_id"] = curse_message.id

        guild_data["channels"][key] = channel.id

store.save("guilds")
