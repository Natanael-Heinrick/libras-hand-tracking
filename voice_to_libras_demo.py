from voice_to_libras import AvatarBridge, GlossMapper, SpeechPipeline


def main():
    pipeline = SpeechPipeline()
    mapper = GlossMapper()
    avatar = AvatarBridge()

    example = "oi tudo bem"
    speech = pipeline.transcribe_text(example)
    gloss_sequence = mapper.map_to_gloss(speech)
    commands = avatar.build_commands(gloss_sequence)

    print("Texto normalizado:", speech.normalized_text)
    print("Glosas:", gloss_sequence.glosses)
    print("Comandos do avatar:", [command.payload for command in commands])


if __name__ == "__main__":
    main()
