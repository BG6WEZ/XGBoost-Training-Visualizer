import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { WebSocketServer } from 'ws'
import http from 'http'

// 加载环境变量
dotenv.config()

const app: express.Application = express()
const PORT = process.env.PORT || 4006

// 中间件
app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok' })
})

// 导入路由
import datasetRoutes from './routes/dataset.routes.js'

// API 路由
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

// 数据集路由
app.use('/api/datasets', datasetRoutes)

// 实验路由
app.get('/api/experiments', (req, res) => {
  res.json({
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    hasNext: false,
    hasPrev: false,
  })
})

// 创建 HTTP 服务器
const server = http.createServer(app)

// WebSocket 服务器
const wss = new WebSocketServer({ server })

wss.on('connection', (ws) => {
  console.log('WebSocket connection established')
  
  ws.on('message', (message) => {
    console.log('Received message:', message)
  })
  
  ws.on('close', () => {
    console.log('WebSocket connection closed')
  })
})

// 启动服务器
server.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`)
  console.log(`WebSocket server running on ws://localhost:${PORT}`)
})

export { app, server }