import { ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { useState } from 'react';

interface Product {
  id: string;
  name: string;
  price: string;
  image: string;
  store: string;
  url: string;
}

interface ShopTheLookProps {
  style?: string;
}

// Mock product data - in a real app, this would come from an API
const generateProducts = (style: string = 'general'): Product[] => {
  const baseProducts = [
    {
      id: '1',
      name: 'Classic Denim Jacket',
      price: '$89.99',
      image: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=300&h=300&fit=crop',
      store: 'Amazon Fashion',
      url: '#',
    },
    {
      id: '2',
      name: 'White Sneakers',
      price: '$65.00',
      image: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=300&h=300&fit=crop',
      store: 'Nike',
      url: '#',
    },
    {
      id: '3',
      name: 'Black Leather Bag',
      price: '$129.99',
      image: 'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=300&h=300&fit=crop',
      store: 'Amazon',
      url: '#',
    },
    {
      id: '4',
      name: 'Minimalist Watch',
      price: '$199.00',
      image: 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=300&h=300&fit=crop',
      store: 'Nordstrom',
      url: '#',
    },
    {
      id: '5',
      name: 'Slim Fit Jeans',
      price: '$79.99',
      image: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=300&h=300&fit=crop',
      store: 'Levi\'s',
      url: '#',
    },
    {
      id: '6',
      name: 'Cotton T-Shirt',
      price: '$24.99',
      image: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=300&h=300&fit=crop',
      store: 'H&M',
      url: '#',
    },
  ];

  return baseProducts;
};

export function ShopTheLook({ style = 'general' }: ShopTheLookProps) {
  const [scrollPosition, setScrollPosition] = useState(0);
  const products = generateProducts(style);

  const scroll = (direction: 'left' | 'right') => {
    const container = document.getElementById('shop-scroll-container');
    if (container) {
      const scrollAmount = 300;
      const newPosition = direction === 'left' 
        ? scrollPosition - scrollAmount 
        : scrollPosition + scrollAmount;
      
      container.scrollTo({ left: newPosition, behavior: 'smooth' });
      setScrollPosition(newPosition);
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Shop the Look</h3>
          <div className="flex gap-2">
            <button
              onClick={() => scroll('left')}
              className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="Scroll left"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            </button>
            <button
              onClick={() => scroll('right')}
              className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="Scroll right"
            >
              <ChevronRight className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div 
          id="shop-scroll-container"
          className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {products.map((product) => (
            <a
              key={product.id}
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 w-44 group"
            >
              <div className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 mb-2">
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                  <ExternalLink className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{product.name}</p>
                <p className="text-sm font-semibold text-pink-600">{product.price}</p>
                <p className="text-xs text-gray-500">{product.store}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
