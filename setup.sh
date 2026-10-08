mkdir -p ~/.streamlit/

echo "\
[server]\n\
port = $PORT\n\
headless = true\n\
enableWebsocketCompression = false\n\
\n\
" > ~/.streamlit/config.toml
