# =======================================
FROM helsinkitest/node:18-slim AS distbase
# =======================================

# Install ca-certificates so that Sentry can upload source maps
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && apt-get clean

# =============================
FROM distbase AS appbase
# =============================

# Build ARGS
ARG PROJECT
ARG FOLDER

# Yarn
ENV YARN_VERSION 1.22.10
ENV YARN_CACHE_FOLDER /app/.yarn_cache
RUN yarn policies set-version "$YARN_VERSION" && \
    yarn config set ignore-engines true

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock lerna.json ./
COPY $PROJECT/$FOLDER/package.json $PROJECT/$FOLDER/package.json
COPY $PROJECT/shared/package.json* $PROJECT/shared/package.json
COPY shared/package.json shared/package.json
RUN --mount=type=cache,target="$PWD/.yarn_cache",sharing=locked YARN_CACHE_FOLDER="$PWD"/.yarn_cache yarn --frozen-lockfile --check-files --network-timeout 600000

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
ARG PROJECT
ARG FOLDER
ARG SENTRY_ORG
ARG SENTRY_PROJECT
ARG SENTRY_AUTH_TOKEN
ARG SENTRY_URL
ARG SENTRY_RELEASE
ARG NEXT_PUBLIC_ASKEM_API_KEY
ARG NEXT_PUBLIC_SHOW_COOKIE_BANNER

# Use non-root user
USER appuser
WORKDIR /app

# copy all files
COPY . .

# Build application
WORKDIR /app/$PROJECT/$FOLDER/

RUN yarn build

# ==========================================
FROM appbase AS production
# ==========================================

ARG PORT
ARG PROJECT
ARG FOLDER
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE

# Use non-root user
USER appuser

WORKDIR /app

# Install production dependencies
RUN rm -rf /app/$PROJECT/$FOLDER/node_modules && yarn install --production --check-files --ignore-scripts --prefer-offline && yarn cache clean --force

# Copy files needed by nextjs
COPY --from=staticbuilder app/$PROJECT/$FOLDER/.next $PROJECT/$FOLDER/.next
COPY --from=staticbuilder app/$PROJECT/$FOLDER/next-i18next.config.js app/$PROJECT/$FOLDER/next.config.js $PROJECT/$FOLDER/
COPY --from=staticbuilder app/next.config.js ./
COPY --from=staticbuilder app/shared/src/server/next-server.js shared/src/server/

# Copy public directory
COPY $PROJECT/$FOLDER/public $PROJECT/$FOLDER/public

ENV NEXT_TELEMETRY_DISABLED 1

USER nobody:0

# Expose port
EXPOSE $PORT

CMD ["sh", "-c", "yarn --cwd $PROJECT/$FOLDER start"]
