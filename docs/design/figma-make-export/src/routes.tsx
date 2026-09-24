import { createBrowserRouter } from 'react-router';
import MainLayout from './layouts/MainLayout';
import StartPage from './pages/StartPage';
import CatalogPage from './pages/CatalogPage';
import OrderPage from './pages/OrderPage';
import AddArtPage from './pages/AddArtPage';
import SignupPage from './pages/SignupPage';
import LoginPage from './pages/LoginPage';
import OrderSentPage from './pages/OrderSentPage';
import MyOrdersPage from './pages/MyOrdersPage';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: MainLayout,
    children: [
      { index: true, Component: StartPage },
      { path: 'catalog', Component: CatalogPage },
      { path: 'order', Component: OrderPage },
      { path: 'add-art', Component: AddArtPage },
      { path: 'signup', Component: SignupPage },
      { path: 'login', Component: LoginPage },
      { path: 'order-sent', Component: OrderSentPage },
      { path: 'my-orders', Component: MyOrdersPage },
    ],
  },
]);
