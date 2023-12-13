# =============================
FROM helsinkitest/node:18-slim AS appbase
# =============================

ARG PROJECT
ARG FOLDER

# Install ca-certificates so that Sentry can upload source maps
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && apt-get clean

# Yarn
ENV YARN_VERSION 1.22.10

RUN yarn policies set-version "$YARN_VERSION" && \
    yarn config set ignore-engines true

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
COPY $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY $PROJECT/shared/package.json* $PROJECT/shared/package.json
COPY shared/package.json shared/package.json
RUN --mount=type=cache,target="$PWD/.yarn_cache",sharing=locked YARN_CACHE_FOLDER="$PWD"/.yarn_cache yarn --frozen-lockfile --check-files --network-timeout 600000

# =============================
FROM appbase AS development
# =============================
ARG PROJECT
ARG FOLDER
# Set V8 max heap size to 2GB (default is 512MB)
# This prevents Docker Compose from crashing due to out of memory errors
ENV NODE_OPTIONS="--max_old_space_size=2048"

WORKDIR /app

# Copy all files
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1
# Bake package.json start command into the image
ENV DEV_START "yarn --cwd $PROJECT/$FOLDER dev"
CMD ["sh", "-c", "${DEV_START}"]

# ===================================
FROM appbase AS staticbuilder
# ===================================

# Set environmental variables for frontend (used in CI)
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_ACTIVATION_LINK_EXPIRATION_SECONDS
ARG NEXT_PUBLIC_MOCK_FLAG
ARG NEXT_PUBLIC_ENABLE_SUOMIFI
ARG NEXT_PUBLIC_DISABLE_VTJ
ARG NEXTJS_DISABLE_SENTRY
ARG NEXTJS_SENTRY_UPLOAD_DRY_RUN
ARG NEXT_PUBLIC_SENTRY_ENVIRONMENT
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_SENTRY_DEDBUG
ARG NEXT_PUBLIC_SENTRY_TRACE_SAMPLE_RATE
ARG NEXTJS_SENTRY_TRACING
ARG NEXT_PUBLIC_LINKEDEVENTS_URL
ARG NEXT_PUBLIC_KEYWORDS_DATA_SOURCE
ARG NEXT_SHARP_PATH
ARG SENTRY_ORG
ARG PROJECT
ARG FOLDER
ARG SENTRY_PROJECT
ARG SENTRY_AUTH_TOKEN
ARG SENTRY_URL
ARG SENTRY_RELEASE
ARG NEXT_PUBLIC_ASKEM_API_KEY
ARG NEXT_PUBLIC_SHOW_COOKIE_BANNER

WORKDIR /app

# copy all files
COPY . .
#COPY --from=appbase --chown=appuser:appuser /app/node_modules ./node_modules

# Build application
WORKDIR /app/$PROJECT/$FOLDER/

RUN yarn build

# Clean all dependencies (this should avoid caching + missing /pages directory problem)
RUN rm -rf node_modules
RUN yarn cache clean

# ==========================================
FROM helsinkitest/node:18-slim AS production
# ==========================================

ARG PORT
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE
ARG PROJECT
ARG FOLDER

WORKDIR /app

# Copy cache
# COPY --from=appbase /app/.yarn_cache ./.yarn_cache

# Copy files needed by yarn install
COPY package.json yarn.lock lerna.json ./
COPY $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY $PROJECT/shared/package.json $PROJECT/shared/package.json
COPY shared/package.json shared/package.json

# Install production dependencies
RUN --mount=type=cache,from=appbase,target="$PWD/.yarn_cache",sharing=locked YARN_CACHE_FOLDER="$PWD"/.yarn_cache  yarn install --production --check-files --ignore-scripts --prefer-offline && yarn cache clean --force

# Copy files needed by nextjs
COPY --from=staticbuilder app/$PROJECT/$FOLDER/.next $PROJECT/$FOLDER/.next
COPY --from=staticbuilder app/$PROJECT/$FOLDER/next-i18next.config.js app/$PROJECT/$FOLDER/next.config.js $PROJECT/$FOLDER/
COPY --from=staticbuilder app/next.config.js ./
COPY --from=staticbuilder app/shared/src/server/next-server.js shared/src/server/

# Copy public directory
COPY $PROJECT/$FOLDER/public $PROJECT/$FOLDER/public

RUN chgrp -R 0 /app && \
    chmod -R g=u /app

# Expose port
EXPOSE $PORT

ENV NEXT_TELEMETRY_DISABLED 1

# Start nextjs server
ENV PROD_START "yarn --cwd $PROJECT/$FOLDER start"
CMD ["sh", "-c", "${PROD_START}"]
