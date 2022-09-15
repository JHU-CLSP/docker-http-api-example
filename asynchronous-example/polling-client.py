import random
import requests
import time


def poll_factorize(url: str):
    done = False
    numbers = [random.randint(2, 2**20) for _ in range(20)]
    while not done:
        done = True
        for n in numbers:
            status = requests.post(url, json={'number': n}).json()

            if status['done']:
                print(f'{n:7d} =', status['factorization_str'])
            else:
                print(f'{n:7d} = ...')

            done = done and status['done']

        if not done:
            print()
            time.sleep(1)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Submit twenty large numbers to be factorized and poll the server until they are done',
    )
    parser.add_argument('url', help='Factorize endpoint URL')
    args = parser.parse_args()

    poll_factorize(args.url)


if __name__ == '__main__':
    main()
