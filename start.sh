#!/bin/bash
cd backend
python -m backend.api.main &
cd ../frontend
npm run dev -- --host
