import { PrismaClient } from '@prisma/client'
import Redis from 'ioredis'
import { Request, Response } from 'express'

// 创建 Prisma 客户端
const prisma = new PrismaClient()

// 创建 Redis 客户端
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
})

export interface Context {
  req: Request
  res: Response
  prisma: PrismaClient
  redis: Redis
}

export { prisma, redis }