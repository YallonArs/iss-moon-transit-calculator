from astropy.coordinates import TETE, SkyCoord, EarthLocation, ITRS, AltAz

__all__ = [
	"transform_TEME_to_TETE",
	"transform_to_altaz"
]


def transform_TEME_to_TETE(coord: SkyCoord, geo: EarthLocation) -> SkyCoord:
	obstime = coord.obstime

	# 2. Transform TEME to geocentric ITRS
	# ITRS (International Terrestrial Reference System) is a frame locked to the rotating Earth
	itrs_geo = coord.transform_to(ITRS(obstime=obstime))

	# 3. Shift the coordinate origin from Earth's center to the observer (Topocentric ITRS)
	# This vector subtraction captures the perspective shift (parallax) cleanly
	topo_itrs_repr = itrs_geo.cartesian.without_differentials() - geo.get_itrs(obstime).cartesian
	itrs_topo = ITRS(topo_itrs_repr, obstime=obstime, location=geo)

	# 4. Transform the local vector to TETE for visible/apparent equatorial coordinates
	# TETE naturally adapts to the true equator and equinox of-date for your specific location
	visible_equatorial = itrs_topo.transform_to(TETE(obstime=obstime, location=geo))

	return visible_equatorial

def transform_to_altaz(coord: SkyCoord, geo: EarthLocation) -> SkyCoord:
	return coord.transform_to(AltAz(obstime=coord.obstime, location=geo))
