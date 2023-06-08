import Header from 'benefit/applicant/components/header/Header';
import TermsOfService from 'benefit/applicant/components/termsOfService/TermsOfService';
import { IS_CLIENT, LOCAL_STORAGE_KEYS } from 'benefit/applicant/constants';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import * as React from 'react';
import useAuth from 'shared/hooks/useAuth';

import { ROUTES } from '../../constants';
import { $Main } from './Layout.sc';

const Footer = dynamic(
  () => import('benefit/applicant/components/footer/Footer'),
  { ssr: true }
);

type Props = { children: React.ReactNode };

const Layout: React.FC<Props> = ({ children, ...rest }) => {
  const { isAuthenticated } = useAuth();
  const [isTermsOfServiceApproved, setIsTermsOfSerivceApproved] =
    React.useState(false);
  const router = useRouter();
  const bgColor = router.pathname === ROUTES.LOGIN ? 'silverLight' : 'white';

  React.useEffect(() => {
    if (IS_CLIENT) {
      setIsTermsOfSerivceApproved(
        // eslint-disable-next-line scanjs-rules/identifier_localStorage
        localStorage.getItem(
          LOCAL_STORAGE_KEYS.IS_TERMS_OF_SERVICE_APPROVED
        ) === 'true'
      );
    }
  }, []);

  return (
    <$Main $backgroundColor={bgColor} {...rest}>
      <Header />
      {isAuthenticated && !isTermsOfServiceApproved ? (
        <TermsOfService
          setIsTermsOfSerivceApproved={setIsTermsOfSerivceApproved}
        />
      ) : (
        children
      )}
      <Footer />
    </$Main>
  );
};

export default Layout;
