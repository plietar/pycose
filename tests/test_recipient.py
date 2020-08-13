from binascii import unhexlify

from pytest import mark

from pycose.attributes import CoseAlgorithm
from pycose.cosebase import HeaderKeys
from pycose.keys.cosekey import CoseKey, EllipticCurveTypes
from pycose.crypto import CoseKDFContext, PartyInfo, SuppPubInfo
from pycose.keys.ec import EC2
from pycose.recipient import CoseRecipient


@mark.parametrize("phdr, uhdr, alg, peer_key, eph_private_key, encoded_phdr, encoded_uhdr, cek, rcpt",
                  [
                      ({HeaderKeys.ALG: CoseAlgorithm.ECDH_ES_HKDF_256},
                       {
                           HeaderKeys.KID: "meriadoc.brandybuck@buckland.example".encode('utf-8')
                       },
                       CoseAlgorithm.A128GCM,
                       EC2(crv=EllipticCurveTypes.P_256,
                           x=CoseKey.base64decode('Ze2loSV3wrroKUN_4zhwGhCqo3Xhu1td4QjeQ5wIVR0'),
                           y=CoseKey.base64decode('HlLtdXARY_f55A3fnzQbPcm6hgr34Mp8p-nuzQCE0Zw')),
                       EC2(crv=EllipticCurveTypes.P_256,
                           d=unhexlify(b'02D1F7E6F26C43D4868D87CEB2353161740AACF1F7163647984B522A848DF1C3')),
                       unhexlify(b'A1013818'),
                       {-1: {1: 2, -1: 1,
                             -2: unhexlify(b'98F50A4FF6C05861C8860D13A638EA56C3F5AD7590BBFBF054E1C7B4D91D6280'),
                             -3: unhexlify(b'F01400B089867804B8E9FC96C3932161F1934F4223069170D924B7E03BF822BB')},
                        4: unhexlify(b'6D65726961646F632E6272616E64796275636B406275636B6C616E642E6578616D706C65')},
                       unhexlify(b'56074D506729CA40C4B4FE50C6439893'),
                       [unhexlify(b'A1013818'),
                        {-1:
                            {
                                1: 2,
                                -1: 1,
                                -2: unhexlify(b'98F50A4FF6C05861C8860D13A638EA56C3F5AD7590BBFBF054E1C7B4D91D6280'),
                                -3: unhexlify(b'F01400B089867804B8E9FC96C3932161F1934F4223069170D924B7E03BF822BB')
                            },
                            4: unhexlify(b'6D65726961646F632E6272616E64796275636B406275636B6C616E642E6578616D706C65')},
                        b'']
                       )
                  ], ids=['test_ecdh_direct_key_derivation_recipient'])
def test_kek_ecdh_direct_recipient(phdr, uhdr, alg, peer_key, eph_private_key, encoded_phdr, encoded_uhdr, cek, rcpt):
    r = CoseRecipient(phdr=phdr, uhdr=uhdr)

    u = PartyInfo()
    v = PartyInfo()
    s = SuppPubInfo(128, r.encode_phdr())
    kdf_ctx = CoseKDFContext(alg, u, v, s)
    kek = r.derive_kek(eph_private_key, public_key=peer_key, alg=phdr[HeaderKeys.ALG], context=kdf_ctx)

    # since this is direct usage --> kek == cek
    assert kek == cek
    assert r.encode_phdr() == encoded_phdr

    eph_key_info = \
        {
            HeaderKeys.EPHEMERAL_KEY:
                EC2(crv=EllipticCurveTypes.P_256,
                    x=unhexlify(b'98F50A4FF6C05861C8860D13A638EA56C3F5AD7590BBFBF054E1C7B4D91D6280'),
                    y=unhexlify(b'F01400B089867804B8E9FC96C3932161F1934F4223069170D924B7E03BF822BB')).encode('crv',
                                                                                                             'x',
                                                                                                             'y')
        }
    r.uhdr_update(eph_key_info)

    assert r.encode_uhdr() == encoded_uhdr

    r.payload = b''
    assert r.encode() == rcpt
