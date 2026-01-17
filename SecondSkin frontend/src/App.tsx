import { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { AnimatePresence } from 'motion/react';
import { SwipeCard } from './components/SwipeCard';
import { StyleBoard } from './components/StyleBoard';
import { DraggableLikedImage } from './components/DraggableLikedImage';
import { CuratedFeed } from './components/CuratedFeed';
import { LandingPage } from './components/LandingPage';
import { ShopTheLook } from './components/ShopTheLook';
import { BoardSwipeView } from './components/BoardSwipeView';
import { Plus, Sparkles, Heart, X } from 'lucide-react';

interface Board {
  id: string;
  name: string;
  images: string[];
}

type ViewType = 'landing' | 'main' | 'boardSwipe';

const initialImages = [
  "https://images.unsplash.com/photo-1651742532474-ea4401a34a10?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwb3V0Zml0JTIwc3RyZWV0JTIwc3R5bGV8ZW58MXx8fHwxNzY4Njc2NzU5fDA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1507297448044-a99b358cd06e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtaW5pbWFsJTIwZmFzaGlvbiUyMGNsb3RoaW5nfGVufDF8fHx8MTc2ODU5NzQzOXww&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1632934330201-a641618914d3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjYXN1YWwlMjBvdXRmaXQlMjBzdHlsZXxlbnwxfHx8fDE3Njg2NzY3NTl8MA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1526632503813-6f479409d7bf?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlbGVnYW50JTIwZmFzaGlvbiUyMHdlYXJ8ZW58MXx8fHwxNzY4Njc2NzYwfDA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1728241965102-94f04643e9af?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aW50YWdlJTIwY2xvdGhpbmclMjBzdHlsZXxlbnwxfHx8fDE3Njg2NzY3NjB8MA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1736555142217-916540c7f1b7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBzdHJlZXR3ZWFyJTIwZmFzaGlvbnxlbnwxfHx8fDE3Njg2NzY3NjF8MA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1635375787414-c25aeeb0c214?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxib2hlbWlhbiUyMGZhc2hpb24lMjBvdXRmaXR8ZW58MXx8fHwxNzY4Njc2NzYxfDA&ixlib=rb-4.1.0&q=80&w=1080",
  "https://images.unsplash.com/photo-1768508665014-7e567bf7fdb2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmb3JtYWwlMjBidXNpbmVzcyUyMGF0dGlyZXxlbnwxfHx8fDE3Njg2NzY3NjF8MA&ixlib=rb-4.1.0&q=80&w=1080",
];

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('landing');
  const [selectedBoard, setSelectedBoard] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [likedImages, setLikedImages] = useState<string[]>([]);
  const [curatedFeed, setCuratedFeed] = useState<string[]>([]);
  const [boards, setBoards] = useState<Board[]>([
    { id: '1', name: 'Street Style', images: [] },
    { id: '2', name: 'Minimal', images: [] },
  ]);
  const [isAnimating, setIsAnimating] = useState(false);

  const handleSwipe = (direction: 'left' | 'right') => {
    if (isAnimating) return;
    
    setIsAnimating(true);
    
    if (direction === 'right') {
      const likedImage = initialImages[currentIndex];
      setLikedImages(prev => [...prev, likedImage]);
      setCuratedFeed(prev => [likedImage, ...prev]);
    }
    
    setTimeout(() => {
      setCurrentIndex(prev => prev + 1);
      setIsAnimating(false);
    }, 300);
  };

  const handleButtonSwipe = (direction: 'left' | 'right') => {
    if (isAnimating || !hasMoreCards) return;
    handleSwipe(direction);
  };

  const handleAddBoard = () => {
    const newBoard: Board = {
      id: Date.now().toString(),
      name: `Board ${boards.length + 1}`,
      images: [],
    };
    setBoards(prev => [...prev, newBoard]);
  };

  const handleDeleteBoard = (id: string) => {
    setBoards(prev => prev.filter(board => board.id !== id));
  };

  const handleRenameBoard = (id: string, newName: string) => {
    setBoards(prev =>
      prev.map(board => (board.id === id ? { ...board, name: newName } : board))
    );
  };

  const handleAddImageToBoard = (boardId: string, image: string) => {
    setBoards(prev =>
      prev.map(board =>
        board.id === boardId
          ? { ...board, images: [...board.images, image] }
          : board
      )
    );
  };

  const handleRemoveImageFromBoard = (boardId: string, imageIndex: number) => {
    setBoards(prev =>
      prev.map(board =>
        board.id === boardId
          ? { ...board, images: board.images.filter((_, i) => i !== imageIndex) }
          : board
      )
    );
  };

  const handleRemoveLikedImage = (index: number) => {
    setLikedImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleLikeFromFeed = (image: string) => {
    if (!likedImages.includes(image)) {
      setLikedImages(prev => [...prev, image]);
    }
  };

  const handleBoardClick = (boardId: string) => {
    setSelectedBoard(boardId);
    setCurrentView('boardSwipe');
  };

  const handleBackToMain = () => {
    setCurrentView('main');
    setSelectedBoard(null);
  };

  const handleLikeFromBoard = (image: string) => {
    setLikedImages(prev => [...prev, image]);
    setCuratedFeed(prev => [image, ...prev]);
  };

  // Landing Page View
  if (currentView === 'landing') {
    return <LandingPage onStart={() => setCurrentView('main')} />;
  }

  // Board Swipe View
  if (currentView === 'boardSwipe' && selectedBoard) {
    const board = boards.find(b => b.id === selectedBoard);
    if (board) {
      return (
        <BoardSwipeView
          boardName={board.name}
          onBack={handleBackToMain}
          onLike={handleLikeFromBoard}
        />
      );
    }
  }

  const hasMoreCards = currentIndex < initialImages.length;

  // Main App View
  return (
    <DndProvider backend={HTML5Backend}>
      <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-pink-500" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
                SecondSkin
              </h1>
            </div>
            <p className="text-sm text-gray-600">Discover your style</p>
          </div>
        </header>

        {/* Shop the Look Bar */}
        <ShopTheLook />

        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Swipe Section */}
          <div className="mb-8">
            <div className="relative w-full max-w-md mx-auto aspect-[3/4]">
              {hasMoreCards ? (
                <>
                  {/* Stack effect - show next card behind */}
                  {currentIndex + 1 < initialImages.length && (
                    <div className="absolute w-full h-full">
                      <div className="w-full h-full rounded-2xl overflow-hidden shadow-xl bg-white scale-95 opacity-50">
                        <img
                          src={initialImages[currentIndex + 1]}
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
                      image={initialImages[currentIndex]}
                      onSwipe={handleSwipe}
                    />
                  </AnimatePresence>
                </>
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-white rounded-2xl shadow-2xl">
                  <div className="text-center p-8">
                    <Sparkles className="w-16 h-16 text-pink-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      No more items!
                    </h3>
                    <p className="text-gray-600">Check out your curated feed below</p>
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

          {/* Liked Images Section */}
          {likedImages.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4 text-gray-900">
                Liked Items ({likedImages.length})
              </h2>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
                {likedImages.map((image, index) => (
                  <DraggableLikedImage
                    key={index}
                    image={image}
                    onRemove={() => handleRemoveLikedImage(index)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Style Boards Section */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Style Boards</h2>
              <button
                onClick={handleAddBoard}
                className="flex items-center gap-2 px-4 py-2 bg-pink-500 hover:bg-pink-600 text-white rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>New Board</span>
              </button>
            </div>
            
            <div className="flex gap-4 overflow-x-auto pb-4">
              {boards.map(board => (
                <StyleBoard
                  key={board.id}
                  id={board.id}
                  name={board.name}
                  images={board.images}
                  onAddImage={(image) => handleAddImageToBoard(board.id, image)}
                  onRemoveImage={(index) => handleRemoveImageFromBoard(board.id, index)}
                  onDelete={() => handleDeleteBoard(board.id)}
                  onRename={(newName) => handleRenameBoard(board.id, newName)}
                  onClick={() => handleBoardClick(board.id)}
                />
              ))}
            </div>
          </div>

          {/* Curated Feed */}
          <CuratedFeed images={curatedFeed} onLike={handleLikeFromFeed} />
        </div>
      </div>
    </DndProvider>
  );
}