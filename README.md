# Authenticated AI Chat

A [streamlit](https://streamlit.io/) application with an
[OpenAI Assistant](https://platform.openai.com/docs/assistants/whats-new) streaming back end.

The application supports authenticating users via a signed url.
So the actual user authentication would be handled by some existing webapp,
which would then generate a time limited signed url for that user and redirect
them to the AI chat application.

# Configuration

`OPENAI_API_KEY` environment variable must be set.
If you use an OpenAI organization, set `OPENAI_ORG_ID`.

Create an OpenAI Assistant using the [assistants dashboard](https://platform.openai.com/assistants).
Configure it with the model to use, any system messages and any files/vector stores it can access
using the [`file_search` tool](https://platform.openai.com/docs/assistants/tools/file-search).

Upload files or vector stores via the [storage dashboard](https://platform.openai.com/storage).

Configure `assistant_id` in [`.streamlit/env.toml`](.streamlit/env.toml).

# Authentication

The chat application must be accessed using a signed url.
Generate a production keypair using `uv run tools/sign.py keys/prod`.
This will generate `keys/prod.key` and `keys/prod.pub`.

Configure `pubkey` in [`.streamlit/env.toml`](.streamlit/env.toml) with `keys/prod.pub`.

`keys/prod.key` will be used by the invoking application to sign the url.
A signed url contains `message=<username>:<unixtime>&signature=<signature>`,
where `unixtime` is UNIX epoch seconds - a time in the future when the url will expire.

See [`tools/sign.py`](tools/sign.py) for example code generating a signature.
This tool can also be used in development to generate a signature, e.g.:

```sh-session
$ uv run tools/sign.py myuser 3000
?message=myuser:1741194947&signature=utITpoOTiBLizon5EjWZ_FZZceecs2hXqioSnvQxvYNL79ec58xC1ubi6OvKgkJesbpC5slNeiV8B9szWMk6Bw==
```

# Development

To run in development, first generate a signed url query string for the user,
see above `uv run tools/sign.py myuser 3000`.

Make sure `OPENAI_API_KEY` is set in the environment.

Run `uv run streamlit run main.py`.
This will launch an unauthenticated url in your browser,
append the signed query string from above and reload.

# Docker

A production mode docker container can be built with:

`docker buildx build -t ai --load .`

and run with:

`docker run --env OPENAI_API_KEY --init --rm -p 8501:8501 ai`
