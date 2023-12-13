# =======================================
FROM helsinkitest/node:18-slim AS distbase
# =======================================

# Install ca-certificates so that Sentry can upload source maps
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && apt-get clean

# Copy all files
COPY --chown=appuser:root . /app

# =============================
FROM distbase AS appbase
# =============================

ARG PROJECT
ARG FOLDER

# Yarn
ENV YARN_VERSION 1.22.10
RUN yarn policies set-version "$YARN_VERSION" && \
    yarn config set ignore-engines true

WORKDIR /app

# Install dependencies
COPY --chown=appuser:root package.json yarn.lock ./
COPY --chown=appuser:root $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY --chown=appuser:root $PROJECT/shared/package.json* $PROJECT/shared/package.json
COPY --chown=appuser:root shared/package.json shared/package.json
RUN YARN_CACHE_FOLDER=/app/.yarn_cache yarn --frozen-lockfile --check-files --network-timeout 600000

# =============================
FROM appbase AS development
# =============================
ARG PROJECT
ARG FOLDER
# Set V8 max heap size to 2GB (default is 512MB)
# This prevents Docker Compose from crashing due to out of memory errors
ENV NODE_OPTIONS="--max_old_space_size=2048"

# Use non-root user
USER appuser

WORKDIR /app

# Copy all files
COPY --chown=appuser:root --from=distbase /app .

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

# Use non-root user
USER appuser
WORKDIR /app

# Copy all files
COPY --chown=appuser:root --from=distbase /app .

# Build application
WORKDIR /app/$PROJECT/$FOLDER/

RUN yarn build

# Clean all dependencies (this should avoid caching + missing /pages directory problem)
#RUN rm -rf node_modules && yarn cache clean

# ==========================================
FROM helsinkitest/node:18-slim AS production
# ==========================================

ARG PORT
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE
ARG PROJECT
ARG FOLDER

# Use non-root user
USER appuser
WORKDIR /app

# Copy cache
COPY --from=appbase /app/.yarn_cache ./.yarn_cache

# Copy files needed by yarn install
COPY --chown=appuser:root package.json yarn.lock lerna.json ./
COPY --chown=appuser:root $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY --chown=appuser:root $PROJECT/shared/package.json $PROJECT/shared/package.json
COPY --chown=appuser:root shared/package.json shared/package.json

# Install production dependencies
RUN YARN_CACHE_FOLDER=/app/.yarn_cache yarn install --production --check-files --ignore-scripts --prefer-offline && yarn cache clean --force

# Copy files needed by nextjs
COPY --from=staticbuilder --chown=appuser:root app/$PROJECT/$FOLDER/.next $PROJECT/$FOLDER/.next
COPY --from=staticbuilder --chown=appuser:root app/$PROJECT/$FOLDER/next-i18next.config.js app/$PROJECT/$FOLDER/next.config.js $PROJECT/$FOLDER/
COPY --from=staticbuilder --chown=appuser:root app/next.config.js ./
COPY --from=staticbuilder --chown=appuser:root app/shared/src/server/next-server.js shared/src/server/

# Copy public directory
COPY --chown=appuser:root $PROJECT/$FOLDER/public $PROJECT/$FOLDER/public

# Expose port
EXPOSE $PORT

ENV NEXT_TELEMETRY_DISABLED 1

# Start nextjs server
ENV PROD_START "yarn --cwd $PROJECT/$FOLDER start"
CMD ["sh", "-c", "${PROD_START}"]
