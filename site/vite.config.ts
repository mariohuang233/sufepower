import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],base:process.env.GITHUB_ACTIONS ? '/sufepower/' : './',publicDir:'../public-data',test:{environment:'jsdom',globals:true}});
