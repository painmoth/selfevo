import React, { useState, useEffect } from 'react'
import './SpriteDisplay.css'

interface SpriteDisplayProps {
  emotion: string | null
  spritePath: string | null
}

const SpriteDisplay: React.FC<SpriteDisplayProps> = ({ emotion, spritePath }) => {
  const [currentSprite, setCurrentSprite] = useState<string>('/img_src/Hitomi/neutral.png')
  const [isTransitioning, setIsTransitioning] = useState(false)

  useEffect(() => {
    const targetPath = spritePath || '/img_src/Hitomi/neutral.png'
    if (targetPath !== currentSprite) {
      setIsTransitioning(true)
      // 短暂延迟后切换，实现淡入淡出效果
      setTimeout(() => {
        setCurrentSprite(targetPath)
        setIsTransitioning(false)
      }, 150)
    }
  }, [spritePath, currentSprite])

  return (
    <div className="sprite-container">
      <img 
        src={currentSprite} 
        alt={emotion || 'character'} 
        className={`sprite-image ${isTransitioning ? 'fade-out' : 'fade-in'}`}
        onError={(e) => {
          // 如果图片加载失败，回退到neutral
          const neutralPath = '/img_src/Hitomi/neutral.png'
          const img = e.target as HTMLImageElement
          if (!img.src.includes('neutral.png')) {
            img.src = neutralPath
          } else {
            // 如果neutral也加载失败，隐藏
            img.style.display = 'none'
          }
        }}
      />
    </div>
  )
}

export default SpriteDisplay
