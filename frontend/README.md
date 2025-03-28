# RecceHub Frontend

A modern web application built with Next.js, React, TypeScript, and Tailwind CSS.

## Technologies

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with animation support
- **UI Components**: Radix UI primitives
- **Form Handling**: React Hook Form with Zod validation
- **State Management**: React Hooks
- **Date Handling**: date-fns
- **Charting**: Recharts
- **Notifications**: Sonner
- **Drag and Drop**: @hello-pangea/dnd

## Development

```bash
# Install dependencies
npm install

# Run the development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run typecheck

# Format code
npm run format:write
```

## Project Structure

- `/src/app`: Next.js App Router pages and layouts
- `/src/components`: Reusable UI components
- `/src/api`: API integration and services
- `/src/hooks`: Custom React hooks
- `/src/lib`: Utility functions and shared logic
- `/src/styles`: Global styles and Tailwind configuration
- `/src/types`: TypeScript type definitions

## Features

- Dark/Light mode support via next-themes
- Responsive design
- Accessible UI components
- Form validation

## Docker

A Dockerfile is included for containerized deployment.
