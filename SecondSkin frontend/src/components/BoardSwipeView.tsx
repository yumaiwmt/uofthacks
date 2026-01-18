import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { SwipeCard } from './SwipeCard';
import { ArrowLeft, Heart, X, Sparkles } from 'lucide-react';

interface BoardSwipeViewProps {
  boardName: string;
  onBack: () => void;
  onLike: (image: string) => void;
}

// Mock curated images based on board style
const getCuratedImages = (boardName: string): string[] => {
  const imagesByStyle: Record<string, string[]> = {
    'Street Style': [
      'https://images.unsplash.com/photo-1651742532474-ea4401a34a10?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
      'https://images.unsplash.com/photo-1736555142217-916540c7f1b7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
      'https://images.unsplash.com/photo-1632934330201-a641618914d3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
      'https://images.unsplash.com/photo-1767799727921-680268a2a1a2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
    ],
    'Minimal': [
      'https://images.unsplash.com/photo-1507297448044-a99b358cd06e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
      'https://images.unsplash.com/photo-1526632503813-6f479409d7bf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
      'https://images.unsplash.com/photo-1654512697655-b2899afacae5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
    ],
  };

  // Return style-specific images or default images
  return imagesByStyle[boardName] || [
    'https://images.unsplash.com/photo-1728241965102-94f04643e9af?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
    'https://images.unsplash.com/photo-1635375787414-c25aeeb0c214?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
    'https://images.unsplash.com/photo-1768508665014-7e567bf7fdb2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080',
  ];
};

export function BoardSwipeView({ boardName, onBack, onLike }: BoardSwipeViewProps) {
  const curatedImages = getCuratedImages(boardName);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const handleSwipe = (direction: 'left' | 'right') => {
    if (isAnimating) return;
    
    setIsAnimating(true);
    
    if (direction === 'right') {
      onLike(curatedImages[currentIndex]);
    }
    
    setTimeout(() => {
      setCurrentIndex(prev => prev + 1);
      setIsAnimating(false);
    }, 300);
  };

  const handleButtonSwipe = (direction: 'left' | 'right') => {
    if (isAnimating || currentIndex >= curatedImages.length) return;
    handleSwipe(direction);
  };

  const hasMoreCards = currentIndex < curatedImages.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-gray-700" />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{boardName}</h1>
              <p className="text-sm text-gray-600">Curated for your style</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Swipe Section */}
        <div className="mb-8">
          <div className="relative w-full max-w-md mx-auto aspect-[3/4]">
            {hasMoreCards ? (
              <>
                {/* Stack effect - show next card behind */}
                {currentIndex + 1 < curatedImages.length && (
                  <div className="absolute w-full h-full">
                    <div className="w-full h-full rounded-2xl overflow-hidden shadow-xl bg-white scale-95 opacity-50">
                      <img
                        src={curatedImages[currentIndex + 1]}
                        alt="Next"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                )}
                
                {/* Current card with AnimatePresence */}
                <AnimatePresence mode="wait">
                  <SwipeCard
                    key={currentIndex}
                    image={curatedImages[currentIndex]}
                    onSwipe={handleSwipe}
                  />
                </AnimatePresence>
              </>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center bg-white rounded-2xl shadow-2xl">
                <div className="text-center p-8">
                  <Sparkles className="w-16 h-16 text-pink-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    You've seen it all!
                  </h3>
                  <p className="text-gray-600 mb-4">
                    No more {boardName} items for now
                  </p>
                  <button
                    onClick={onBack}
                    className="px-6 py-2 bg-pink-500 hover:bg-pink-600 text-white rounded-lg transition-colors"
                  >
                    Back to Boards
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {hasMoreCards && (
            <div className="flex items-center justify-center gap-6 mt-8">
              <button
                onClick={() => handleButtonSwipe('left')}
                disabled={isAnimating}
                className="w-16 h-16 rounded-full bg-white shadow-lg hover:shadow-xl transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center border-2 border-red-200 hover:border-red-400"
              >
                <X className="w-8 h-8 text-red-500" strokeWidth={2.5} />
              </button>
              
              <button
                onClick={() => handleButtonSwipe('right')}
                disabled={isAnimating}
                className="w-16 h-16 rounded-full bg-white shadow-lg hover:shadow-xl transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center border-2 border-green-200 hover:border-green-400"
              >
                <Heart className="w-8 h-8 text-green-500" fill="currentColor" />
              </button>
            </div>
          )}

          <p className="text-center mt-6 text-gray-600">
            Swipe right to like • Swipe left to pass
          </p>
        </div>
      </div>
    </div>
  );
}
