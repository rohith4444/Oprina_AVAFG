import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/common/Button';
import { Mic, Mail, MessageSquare, RefreshCcw } from 'lucide-react';

const HomePage: React.FC = () => {
  return (
    <div className="w-full bg-white">
      {/* Hero Section */}
      <div className="w-full px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            <span>Oprina</span>
          </h1>
          <p className="mt-4 text-2xl font-semibold bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] text-transparent bg-clip-text">
            Voice-Powered Gmail Assistant
          </p>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Manage your inbox through natural conversation with an intelligent, visual assistant
          </p>
          <div className="mt-10 flex items-center justify-center">
            <Link to="/signup">
              <Button size="lg">Try Oprina</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="w-full bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] text-transparent bg-clip-text">
              Smarter Inbox Management
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to manage your email hands-free
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Oprina combines advanced AI voice recognition with Gmail integration to create a seamless, 
              intuitive email management experience.
            </p>
          </div>
          
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid grid-cols-1 gap-x-8 gap-y-10 lg:grid-cols-4">
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-black">
                    <Mic className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Voice-Powered Interaction
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">
                  Simply speak naturally to Oprina to read, summarize, compose, and send emails.
                </dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-black">
                    <Mail className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Seamless Gmail Integration
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">
                  Connect directly to your Gmail account to access all your emails and contacts.
                </dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-black">
                    <MessageSquare className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Animated Avatar Interface
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">
                  Interact with a lifelike animated avatar that responds both visually and verbally.
                </dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-black">
                    <RefreshCcw className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                  Intelligent Management
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">
                  Let Oprina help you prioritize and respond to emails using AI-powered understanding.
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
      
      {/* CTA Section */}
      <div className="w-full bg-white">
        <div className="mx-auto max-w-7xl py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="relative isolate overflow-hidden bg-gray-900 px-6 pt-16 shadow-2xl sm:rounded-3xl sm:px-16 md:pt-24 lg:flex lg:gap-x-20 lg:px-24 lg:pt-0">
            <svg
              viewBox="0 0 1024 1024"
              className="absolute left-1/2 top-1/2 -z-10 h-[64rem] w-[64rem] -translate-y-1/2 [mask-image:radial-gradient(closest-side,white,transparent)] sm:left-full sm:-ml-80 lg:left-1/2 lg:ml-0 lg:-translate-x-1/2 lg:translate-y-0"
              aria-hidden="true"
            >
              <circle cx={512} cy={512} r={512} fill="url(#gradient)" fillOpacity="0.7" />
              <defs>
                <radialGradient id="gradient">
                  <stop stopColor="#5B7CFF" />
                  <stop offset="0.5" stopColor="#4FD1C5" />
                  <stop offset="1" stopColor="#4ADE80" />
                </radialGradient>
              </defs>
            </svg>
            <div className="mx-auto max-w-md text-center lg:mx-0 lg:flex-auto lg:py-32 lg:text-left">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Boost your productivity with voice.
                <br />
                Start using Oprina today.
              </h2>
              <p className="mt-6 text-lg leading-8 text-gray-300">
                Stop wasting time managing emails. Let Oprina do the work while you focus on what really matters.
              </p>
              <div className="mt-10 flex items-center justify-center lg:justify-start">
                <Link to="/signup">
                  <Button>Get started</Button>
                </Link>
              </div>
            </div>
            <div className="relative mt-16 h-80 lg:mt-8">
              <div className="absolute left-0 top-0 w-[57rem] max-w-none rounded-md bg-white/5 ring-1 ring-white/10">
                <div className="h-[300px] w-full bg-gradient-to-r from-[#5B7CFF]/20 via-[#4FD1C5]/20 to-[#4ADE80]/20 rounded-lg flex items-center justify-center">
                  <div className="w-32 h-32 rounded-full bg-white border-4 border-black flex items-center justify-center relative">
                    <div className="w-24 h-24 rounded-full bg-black absolute"></div>
                    <div className="w-16 h-16 rounded-full bg-white absolute"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;