All the config is in .vitepress/config.mjs


# From Docker
docker build --no-cache -t vitepress-inventory .


# From CLI
## depending on the modifications, a build can be necessary
npx vitepress build


## run
npx vitepress dev --host 0.0.0.0 --port 8080
