import click
import os
from node.utils import hardware
from node.utils import audio

@click.command()
@click.option('--file', '-f', help='File name')
@click.option('--speaker_index', '-s', default=0, help='Index of the speaker to play with')
@click.option('--list_speakers', '-ls', is_flag=True, help='List speakers')
def main(file, speaker_index, list_speakers):

    if list_speakers:
        hardware.list_speakers()

    if not os.path.exists(file):
        raise RuntimeError('File does not exist')

    audio.play_audio_file(file)

if __name__ == '__main__':
    main()