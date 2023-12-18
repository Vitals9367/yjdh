# =======================================
FROM helsinkitest/node:18-slim AS distbase
# =======================================

# Install ca-certificates so that Sentry can upload source maps
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && apt-get clean

# ===================================
FROM distbase AS staticbuilder
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
# Copy all files
COPY . .

ENV NODE_OPTIONS="--max_old_space_size=2048"
ENV YARN_VERSION 1.22.10
ENV YARN_CACHE_FOLDER /app/.yarn_cache

RUN yarn policies set-version "$YARN_VERSION" && \
    yarn config set ignore-engines true && \
    yarn --frozen-lockfile --check-files --network-timeout 600000

# Build application
WORKDIR /app/$PROJECT/$FOLDER/
RUN yarn build && rm -rf node_modules

# ==========================================
FROM helsinkitest/node:18-slim AS production
# ==========================================

ARG PORT
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE
ARG PROJECT
ARG FOLDER

WORKDIR /app

# Copy files needed by yarn install
COPY --chown=appuser:appuser package.json yarn.lock lerna.json ./
COPY --chown=appuser:appuser $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY --chown=appuser:appuser $PROJECT/shared/package.json $PROJECT/shared/package.json
COPY --chown=appuser:appuser shared/package.json shared/package.json

# Install production dependencies
RUN yarn install --production --check-files --ignore-scripts --prefer-offline && yarn cache clean --force

# Copy files needed by nextjs
COPY --from=staticbuilder --chown=appuser:appuser app/$PROJECT/$FOLDER/.next $PROJECT/$FOLDER/.next
COPY --from=staticbuilder --chown=appuser:appuser app/$PROJECT/$FOLDER/next-i18next.config.js app/$PROJECT/$FOLDER/next.config.js $PROJECT/$FOLDER/
COPY --from=staticbuilder --chown=appuser:appuser app/next.config.js ./
COPY --from=staticbuilder --chown=appuser:appuser app/shared/src/server/next-server.js shared/src/server/

# Copy public directory
COPY $PROJECT/$FOLDER/public $PROJECT/$FOLDER/public

ENV NEXT_TELEMETRY_DISABLED 1

# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0

# Expose port
EXPOSE $PORT

CMD ["sh", "-c", "yarn --cwd $PROJECT/$FOLDER start"]
