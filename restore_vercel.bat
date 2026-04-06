@echo off
git add requirements.txt runtime.txt
git commit -m "fix: restore requirements.txt and runtime.txt for Vercel deployment"
git push origin main
