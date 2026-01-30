import React, { useState } from 'react'
import axios from 'axios'
import './FeedbackModal.css'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  task: string
  response: string
  sessionId: string | null
  onFeedbackSubmitted?: () => void
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  task,
  response,
  sessionId,
  onFeedbackSubmitted
}) => {
  const [satisfaction, setSatisfaction] = useState(5)
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedbackReport, setFeedbackReport] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (!sessionId) {
      alert('会话ID不存在，无法提交反馈')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await axios.post('/api/feedback', {
        task: task,
        response: response,
        satisfaction: satisfaction,
        description: description || undefined,
        session_id: sessionId
      })

      if (result.data.success) {
        setFeedbackReport(result.data.feedback_report)
        if (onFeedbackSubmitted) {
          onFeedbackSubmitted()
        }
      } else {
        alert(`提交反馈失败: ${result.data.message}`)
      }
    } catch (error: any) {
      console.error('提交反馈失败:', error)
      alert(`提交反馈失败: ${error?.response?.data?.detail || error?.message || '未知错误'}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setSatisfaction(5)
    setDescription('')
    setFeedbackReport(null)
    onClose()
  }

  return (
    <div className="feedback-modal-overlay" onClick={handleClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="feedback-modal-header">
          <h2>反馈收集</h2>
          <button className="close-button" onClick={handleClose}>×</button>
        </div>

        {!feedbackReport ? (
          <div className="feedback-modal-content">
            <div className="feedback-section">
              <label>任务:</label>
              <div className="task-preview">{task}</div>
            </div>

            <div className="feedback-section">
              <label>Agent回复:</label>
              <div className="response-preview">{response.substring(0, 300)}{response.length > 300 ? '...' : ''}</div>
            </div>

            <div className="feedback-section">
              <label>满意度评分 (1-10):</label>
              <div className="satisfaction-input">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={satisfaction}
                  onChange={(e) => setSatisfaction(Number(e.target.value))}
                  className="satisfaction-slider"
                />
                <span className="satisfaction-value">{satisfaction}/10</span>
              </div>
            </div>

            <div className="feedback-section">
              <label>文字反馈 (可选):</label>
              <textarea
                className="feedback-textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="请描述您对本次回复的反馈..."
                rows={4}
              />
            </div>

            <div className="feedback-modal-actions">
              <button
                className="submit-button"
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? '提交中...' : '提交反馈'}
              </button>
              <button className="cancel-button" onClick={handleClose}>
                取消
              </button>
            </div>
          </div>
        ) : (
          <div className="feedback-modal-content">
            <div className="feedback-success">
              <h3>反馈已提交！</h3>
              {satisfaction < 7 && (
                <p className="evolution-notice">
                  ⚠️ 满意度较低，已触发Agent进化机制
                </p>
              )}
              <div className="feedback-report">
                <h4>反馈分析报告:</h4>
                <div className="report-content">{feedbackReport}</div>
              </div>
              <button className="close-button-primary" onClick={handleClose}>
                关闭
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FeedbackModal
