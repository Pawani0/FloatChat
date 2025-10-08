import { FC } from 'react';

interface HeaderProps {
  lastUpdated: string;
}

export const Header: FC<HeaderProps> = ({ lastUpdated }) => {
  return (
    <header className="bg-gray-900/50 text-white py-2 shadow-xl mb-4">
      <div className="container-fluid mx-auto px-4">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h1 className="text-2xl font-bold flex items-center">
              <i className="fas fa-water mr-2 text-cyan-400"></i>
              Indian Ocean Argo Explorer
            </h1>
            <p className="text-sm opacity-75">
              <i className="far fa-clock mr-2"></i>
              Last Updated: {lastUpdated}
            </p>
          </div>
          <div className="hidden md:flex items-center space-x-4 text-xl opacity-75">
            <i className="fas fa-satellite-dish"></i>
            <i className="fas fa-anchor"></i>
            <i className="fas fa-ship"></i>
          </div>
        </div>
      </div>
    </header>
  );
};
