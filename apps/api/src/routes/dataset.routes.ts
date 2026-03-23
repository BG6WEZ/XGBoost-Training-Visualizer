import express from 'express'
import multer from 'multer'
import { v4 as uuidv4 } from 'uuid'
import fs from 'fs'
import path from 'path'

const router: express.Router = express.Router()

// 配置上传目录
const uploadDir = path.join(process.cwd(), 'uploads')
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true })
}

// 配置 multer 存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir)
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = `${uuidv4()}-${Date.now()}`
    const ext = path.extname(file.originalname)
    cb(null, `${path.basename(file.originalname, ext)}-${uniqueSuffix}${ext}`)
  }
})

const upload = multer({ storage })

// 数据上传接口
router.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' })
  }

  const file = req.file
  
  // 检查文件大小
  const maxFileSize = 1024 * 1024 * 1024 // 1GB
  if (file.size > maxFileSize) {
    // 大文件需要切分处理
    return res.json({
      success: true,
      message: 'Large file detected, will be processed in chunks',
      fileId: uuidv4(),
      fileName: file.originalname,
      fileSize: file.size
    })
  }

  // 正常文件处理
  res.json({
    success: true,
    data: {
      id: uuidv4(),
      name: file.originalname,
      filePath: file.path,
      fileSize: file.size,
      fileType: path.extname(file.originalname).slice(1),
      uploadedAt: new Date().toISOString()
    }
  })
})

// 多文件上传
router.post('/upload-multiple', upload.array('files', 10), (req, res) => {
  if (!req.files || !Array.isArray(req.files)) {
    return res.status(400).json({ error: 'No files uploaded' })
  }

  const files = req.files as Express.Multer.File[]
  const uploadedFiles = files.map(file => ({
    id: uuidv4(),
    name: file.originalname,
    filePath: file.path,
    fileSize: file.size,
    fileType: path.extname(file.originalname).slice(1),
    uploadedAt: new Date().toISOString()
  }))

  res.json({
    success: true,
    data: uploadedFiles
  })
})

// 数据预览接口
router.get('/:id/preview', (req, res) => {
  const { id } = req.params
  
  // 模拟数据预览
  res.json({
    success: true,
    data: {
      columns: ['timestamp', 'building_id', 'energy_consumption', 'temperature', 'humidity'],
      rows: [
        ['2024-01-01 00:00:00', 'B001', 120.5, 22.5, 45],
        ['2024-01-01 01:00:00', 'B001', 118.2, 22.3, 46],
        ['2024-01-01 02:00:00', 'B001', 115.8, 22.1, 47],
        ['2024-01-01 03:00:00', 'B001', 112.3, 21.9, 48],
        ['2024-01-01 04:00:00', 'B001', 110.1, 21.8, 49]
      ],
      totalRows: 1000,
      sampleSize: 5
    }
  })
})

// 数据集列表接口
router.get('/', (req, res) => {
  // 模拟数据集列表
  res.json({
    success: true,
    data: {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      hasNext: false,
      hasPrev: false
    }
  })
})

// 数据集详情接口
router.get('/:id', (req, res) => {
  const { id } = req.params
  
  // 模拟数据集详情
  res.json({
    success: true,
    data: {
      id,
      name: 'Building Energy Data',
      fileType: 'csv',
      fileSize: 1048576, // 1MB
      rowCount: 1000,
      columnCount: 5,
      columns: [
        { name: 'timestamp', type: 'datetime' },
        { name: 'building_id', type: 'string' },
        { name: 'energy_consumption', type: 'number' },
        { name: 'temperature', type: 'number' },
        { name: 'humidity', type: 'number' }
      ],
      status: 'completed',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  })
})

// 删除数据集
router.delete('/:id', (req, res) => {
  const { id } = req.params
  
  // 模拟删除操作
  res.json({
    success: true,
    message: 'Dataset deleted successfully'
  })
})

export default router