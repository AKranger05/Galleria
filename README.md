# Serverless Photo Gallery — AWS Project

A fully serverless photo gallery web app built on AWS. Users can sign up, log in,
upload photos, view them in a gallery, and delete them — with automatic
thumbnail generation happening in the background via an event-driven pipeline.

No servers were provisioned or managed to build this. Everything scales
automatically and costs close to nothing at low usage thanks to AWS's
pay-per-request pricing model.

## Features

- **Authentication** — Sign up / log in with email + password via Amazon Cognito
- **Upload** — Direct-to-S3 upload using pre-signed URLs (no file ever passes through a server)
- **Automatic thumbnail generation** — An S3 upload event triggers a Lambda function that processes the image and stores a copy in a separate thumbnail bucket
- **Gallery view** — Each user sees only their own uploaded images
- **Delete** — Removes the image from both S3 buckets and its metadata from DynamoDB
- **Per-user data isolation** — Every image is tagged with the uploader's Cognito user ID

## Architecture

```
                     ┌─────────────────┐
   Browser  ───────▶ │  Amazon Cognito  │  (Sign up / Login)
                     └─────────────────┘
                              │ (JWT token)
                              ▼
                     ┌─────────────────┐
   Browser  ───────▶ │   API Gateway    │  (Cognito Authorizer on every route)
                     └─────────────────┘
                        │        │        │
                 GET /upload  GET /images  DELETE /images/{id}
                        │        │        │
                        ▼        ▼        ▼
                    ┌───────┐┌───────┐┌───────┐
                    │Lambda ││Lambda ││Lambda │
                    │upload ││ list  ││delete │
                    │  url  ││images ││ image │
                    └───────┘└───────┘└───────┘
                        │        │        │
                        ▼        ▼        ▼
                 ┌────────────────────────────┐
                 │   S3 (uploads)  DynamoDB    │
                 └────────────────────────────┘
                        │
                        │ (S3 upload event trigger)
                        ▼
                 ┌───────────────────┐
                 │  Lambda            │
                 │  thumbnail-        │
                 │  generator         │
                 └───────────────────┘
                        │
                        ▼
                 ┌───────────────────┐
                 │  S3 (thumbnails)   │
                 └───────────────────┘
```

## AWS Services Used

| Service | Purpose |
|---|---|
| **Amazon Cognito** | User authentication (sign up, login, JWT tokens) |
| **Amazon S3** | Storage for original images, thumbnails, and the static frontend website |
| **AWS Lambda** | Three functions handling upload URLs, listing images, and deletion, plus one for automatic thumbnail generation |
| **Amazon API Gateway** | REST API exposing the Lambda functions to the frontend, secured with a Cognito authorizer |
| **Amazon DynamoDB** | Stores image metadata (filename, owner, URLs, upload date) |
| **Amazon CloudWatch** | Logs and monitors all Lambda executions |

## Project Structure

```
.
├── frontend/
│   └── index.html                     # Single-page frontend (HTML/CSS/JS, no framework)
├── lambda-functions/
│   ├── gallery-get-upload-url.py      # Generates a pre-signed S3 upload URL
│   ├── gallery-list-images.py         # Returns the logged-in user's images
│   ├── gallery-delete-image.py        # Deletes an image (S3 + DynamoDB)
│   └── gallery-thumbnail-generator.py # Triggered by S3 upload events; creates thumbnails
└── README.md
```

## How It Works

1. **Sign up / Login** — The frontend redirects to Cognito's Hosted UI. After a
   successful login, Cognito redirects back with an authorization code, which
   is exchanged for a JWT ID token.
2. **Upload** — The frontend calls `GET /upload`, which returns a pre-signed S3
   URL scoped to `{userId}/{filename}`. The browser then uploads the file
   directly to S3 using that URL.
3. **Thumbnail generation** — The S3 upload triggers `gallery-thumbnail-generator`,
   which copies the image into the thumbnails bucket and writes a metadata
   record to DynamoDB tagged with the uploader's user ID.
4. **Gallery** — The frontend calls `GET /images`. The Lambda function scans
   DynamoDB for items belonging to the logged-in user and returns temporary
   signed URLs so the (privately-stored) images can be viewed in the browser.
5. **Delete** — The frontend calls `DELETE /images/{id}`. The Lambda function
   verifies the image belongs to the requesting user, then removes it from
   both S3 buckets and DynamoDB.

Every API route is protected by a Cognito authorizer at the API Gateway level,
so only authenticated requests reach the Lambda functions.

## Deployment Notes

- Both S3 storage buckets (uploads and thumbnails) are kept **private** —
  images are only ever accessed through short-lived pre-signed URLs.
- Only the frontend hosting bucket is public (required for static website hosting).
- All services used are within the AWS Free Tier for the usage levels in this project.

## What I Learned

- Designing an event-driven, fully serverless architecture (S3 → Lambda → DynamoDB)
- Securing a REST API with Cognito-based JWT authorization
- Working with pre-signed URLs for direct, secure client-to-S3 uploads
- Debugging real IAM permission and CORS issues in a live AWS environment
- Structuring per-user data isolation without managing a traditional backend server

## Author

Built by Akshat as part of an AWS Cloud Computing training project.
