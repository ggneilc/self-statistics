#!/usr/bin/bash

ENV="$1"   # first argument

if [[ "$ENV" == "dev" ]]; then
    export DJANGO_SETTINGS_MODULE=selfstats.settings.dev

elif [[ "$ENV" == "prod" ]]; then
    export DJANGO_SETTINGS_MODULE=selfstats.settings.prod

else
    echo "Usage: load_env {dev|prod}"
    return 1 2>/dev/null || exit 1
fi

echo "Environment loaded: $DJANGO_SETTINGS_MODULE"
