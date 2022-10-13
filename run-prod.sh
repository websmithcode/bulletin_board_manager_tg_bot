docker run --rm -d \
      -v "${PWD}/db:/app/db" \
      --mount type=bind,source="$(pwd)"/config.ini,target=/app/config.ini \
       bulletin_bot